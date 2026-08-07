#!/usr/bin/env python3
"""mail-declutter — safe inbox cleanup + unsubscribe over IMAP (Gmail & Yahoo).

No API project / OAuth needed — just an app password. Deletions MOVE to Trash/Bin
(recoverable), never permanent. Unsubscribes use RFC-8058 one-click POST or mailto.

Two ways to use it:
  • Guided (no flags to remember):   python3 gmail_cleanup.py wizard
  • Direct commands:                 counts | profile | unsub-list | sweep | unsub-run
Add --provider gmail|yahoo (default: gmail).

First run with no credentials will offer to walk you through setup.
"""
import argparse, imaplib, os, re, subprocess, sys, time, smtplib, getpass, datetime
from collections import Counter
from email.mime.text import MIMEText
from urllib.parse import unquote

# ---------------------------------------------------------------- providers ----
PROVIDERS = {
    "gmail": {
        "imap": "imap.gmail.com", "smtp": "smtp.gmail.com",
        "backend": "gmail", "mailbox_attr": "\\All", "mailbox_fallback": "[Gmail]/All Mail",
        "kc": "gmail_cleanup", "kc_addr": "gmail_cleanup_addr",
        "env_addr": "GMAIL_ADDR", "env_pw": "GMAIL_APP_PASSWORD",
        "apppw_url": "https://myaccount.google.com/apppasswords",
        "setup": ["Turn ON 2-Step Verification: https://myaccount.google.com/security",
                  "Create an app password: https://myaccount.google.com/apppasswords",
                  "  → name it 'mail-declutter', copy the 16-character code",
                  "IMAP is already on for modern Gmail (no toggle needed)."],
    },
    "yahoo": {
        "imap": "imap.mail.yahoo.com", "smtp": "smtp.mail.yahoo.com",
        "backend": "imap", "mailbox_attr": None, "mailbox_fallback": "INBOX",
        "kc": "yahoo_cleanup", "kc_addr": "yahoo_cleanup_addr",
        "env_addr": "YAHOO_ADDR", "env_pw": "YAHOO_APP_PASSWORD",
        "apppw_url": "https://login.yahoo.com/account/security",
        "setup": ["Turn ON 2-Step Verification: https://login.yahoo.com/account/security",
                  "Create an app password: same page → 'Create app password' under",
                  "  'External connections' → name it 'mail-declutter', copy the code.",
                  "Confirm IMAP is on: Yahoo Mail → Settings → More Settings → Mailboxes."],
    },
}

# safety defaults (apply to every provider)
PROTECT_SENDERS = ["google.com", "gmail.com", "yahoo.com", "amazon.com", "amazon.in",
                   "github.com", "apple.com", "microsoft.com", "paypal.com", "gov.in", "nic.in"]
PROTECT_KW = ["receipt", "invoice", "order", "booking", "reservation", "ticket",
              "statement", "tax", "refund", "payment", "confirmation"]


# --------------------------------------------------------------- credentials ---
def _keychain(service, account):
    if sys.platform != "darwin":
        return ""
    try:
        return subprocess.run(["security", "find-generic-password", "-s", service, "-a", account,
                               "-w"], capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""


def _keychain_store(service, account, secret):
    if sys.platform != "darwin":
        return False
    subprocess.run(["security", "add-generic-password", "-U", "-s", service, "-a", account,
                    "-w", secret], capture_output=True)
    return True


def _credfile(provider):
    d = os.path.expanduser("~/.config/mail-declutter")
    return os.path.join(d, "%s.creds" % provider)


def load_creds(provider):
    P = PROVIDERS[provider]
    addr = os.environ.get(P["env_addr"]) or _keychain(P["kc_addr"], "account")
    pw = os.environ.get(P["env_pw"]) or (_keychain(P["kc"], addr) if addr else "")
    if not (addr and pw) and os.path.exists(_credfile(provider)):
        try:
            kv = dict(l.strip().split("=", 1) for l in open(_credfile(provider)) if "=" in l)
            addr = addr or kv.get("addr", "")
            pw = pw or kv.get("app_password", "")
        except Exception:
            pass
    return (addr or ""), (pw or "").replace(" ", "")


def save_creds(provider, addr, pw):
    """Prefer Keychain on macOS; else a 0600 file. Returns where it stored."""
    if _keychain_store(PROVIDERS[provider]["kc"], addr, pw):
        _keychain_store(PROVIDERS[provider]["kc_addr"], "account", addr)
        return "macOS Keychain"
    path = _credfile(provider)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("addr=%s\napp_password=%s\n" % (addr, pw))
    os.chmod(path, 0o600)
    return path


# ---------------------------------------------------------------------- imap ---
def connect(provider, addr, pw, readonly=True):
    P = PROVIDERS[provider]
    M = imaplib.IMAP4_SSL(P["imap"])
    M.login(addr, pw.replace(" ", ""))
    mailbox = P["mailbox_fallback"]
    trash = "Trash"
    for b in (M.list()[1] or []):
        s = b.decode(errors="ignore")
        name = s.split(' "/" ')[-1].strip().strip('"') if ' "/" ' in s else s.rsplit(" ", 1)[-1].strip('"')
        if P["mailbox_attr"] and P["mailbox_attr"] in s:
            mailbox = name
        if "\\Trash" in s or name.lower() in ("trash", "bin", "deleted", "[gmail]/bin", "[gmail]/trash"):
            trash = name
    M._prov, M._mailbox, M._trash = provider, mailbox, trash
    M.select('"%s"' % mailbox, readonly=readonly)
    return M


def _imap_date(days):
    d = datetime.date.today() - datetime.timedelta(days=days)
    return d.strftime("%d-%b-%Y")


def search_bulk(M, days=365):
    """UIDs of old messages that carry an unsubscribe header (the bulk-mail signal)."""
    if PROVIDERS[M._prov]["backend"] == "gmail":
        q = ("older_than:%dd unsubscribe -is:starred -{%s} %s"
             % (days, " ".join(PROTECT_KW), " ".join("-from:%s" % d for d in PROTECT_SENDERS)))
        t, d = M.uid('search', 'X-GM-RAW', '"%s"' % q)
    else:  # standard IMAP
        t, d = M.uid('search', None, 'BEFORE', _imap_date(days), 'HEADER', 'List-Unsubscribe', '""')
    return d[0].split() if d and d[0] else []


def search_sender(M, domain, days=365):
    if PROVIDERS[M._prov]["backend"] == "gmail":
        t, d = M.uid('search', 'X-GM-RAW', '"from:%s older_than:%dd"' % (domain, days))
    else:
        t, d = M.uid('search', None, 'FROM', domain, 'BEFORE', _imap_date(days))
    return d[0].split() if d and d[0] else []


def fetch_from(M, uids):
    dom = Counter()
    for i in range(0, len(uids), 400):
        t, fd = M.uid('fetch', b','.join(uids[i:i + 400]), '(BODY.PEEK[HEADER.FIELDS (FROM)])')
        for it in fd:
            if isinstance(it, tuple):
                raw = it[1].decode('utf-8', 'ignore')
                m = re.search(r'<([^>]+)>', raw) or re.search(r'([\w.\-+]+@[\w.\-]+)', raw)
                if m:
                    dom[m.group(1).split('@')[-1].lower()] += 1
    return dom


def unsub_method(M, domain):
    ids = search_sender(M, domain, days=1000)
    if not ids:
        return ('none', '')
    t, h = M.uid('fetch', ids[-1], '(BODY.PEEK[HEADER.FIELDS (List-Unsubscribe List-Unsubscribe-Post)])')
    hdr = ''.join(x[1].decode('utf-8', 'ignore') for x in h if isinstance(x, tuple))
    lu = re.findall(r'<([^>]+)>', hdr)
    oc = 'One-Click' in hdr
    https = [u for u in lu if u.startswith('http')]
    mailto = [u for u in lu if u.startswith('mailto')]
    if https and oc:
        return ('1click', https[0])
    if mailto:
        return ('mailto', mailto[0])
    if https:
        return ('weblink', https[0])
    return ('none', '')


def move_to_trash(M, uids, batch=300):
    moved = 0
    for i in range(0, len(uids), batch):
        chunk = uids[i:i + batch]
        try:
            M.uid('MOVE', b','.join(chunk), '"%s"' % M._trash)
        except imaplib.IMAP4.error:  # server without MOVE → COPY + delete + expunge
            M.uid('COPY', b','.join(chunk), '"%s"' % M._trash)
            M.uid('STORE', b','.join(chunk), '+FLAGS', '(\\Deleted)')
            M.expunge()
        moved += len(chunk)
        time.sleep(1.2)
    return moved


# ---------------------------------------------------------- creds bootstrap ----
def ensure_creds(provider, interactive=True):
    addr, pw = load_creds(provider)
    if addr and pw:
        return addr, pw
    if not interactive:
        sys.exit("No credentials for %s. Run: python3 %s setup --provider %s"
                 % (provider, os.path.basename(sys.argv[0]), provider))
    return run_setup(provider)


def run_setup(provider):
    P = PROVIDERS[provider]
    print("\n=== Set up %s ===" % provider.title())
    print("You need an APP PASSWORD (not your normal password). Steps:\n")
    for i, s in enumerate(P["setup"], 1):
        print("  %d. %s" % (i, s) if not s.startswith("  ") else "     %s" % s.strip())
    print()
    addr = input("Your %s address: " % provider).strip()
    pw = getpass.getpass("Paste the app password (hidden): ").replace(" ", "")
    print("Verifying...")
    try:
        M = connect(provider, addr, pw, readonly=True)
        M.logout()
    except Exception as e:
        sys.exit("Login failed: %s\nDouble-check the app password and try again." % str(e)[:80])
    where = save_creds(provider, addr, pw)
    print("Stored securely in %s. You're set." % where)
    return addr, pw


# --------------------------------------------------------------- commands ------
def cmd_counts(M):
    P = PROVIDERS[M._prov]
    if P["backend"] == "gmail":
        def n(q):
            t, d = M.uid('search', 'X-GM-RAW', '"%s"' % q)
            return len(d[0].split()) if d and d[0] else 0
        for q, lbl in [("category:promotions", "promotions"),
                        ("category:updates", "updates (holds receipts!)"),
                        ("category:social", "social"), ("category:forums", "forums")]:
            print("%-28s %d" % (lbl, n(q)))
    else:
        t, d = M.uid('search', None, 'ALL'); total = len(d[0].split()) if d and d[0] else 0
        print("%-28s %d" % ("total in %s" % M._mailbox, total))
    print("%-28s %d" % ("bulk (old + unsubscribe)", len(search_bulk(M))))


def cmd_profile(M, top):
    uids = search_bulk(M)
    dom = fetch_from(M, uids)
    print("bulk candidates: %d   distinct senders: %d\n" % (len(uids), len(dom)))
    for d, c in dom.most_common(top):
        print("%-34s %d" % (d, c))


def cmd_unsub_list(M, top):
    dom = fetch_from(M, search_bulk(M))
    print("%-34s %5s  %s" % ("SENDER", "#MSG", "METHOD")); print("-" * 54)
    for d, c in dom.most_common(top):
        meth, _ = unsub_method(M, d)
        print("%-34s %5d  %s" % (d, c, meth))


def _is_protected(domain):
    return any(p in domain for p in PROTECT_SENDERS)


def cmd_sweep(provider, addr, pw, senders, days, yes):
    M = connect(provider, addr, pw, readonly=True)
    targets = [s.strip() for s in senders.split(",") if s.strip()] if senders else \
        [d for d, _ in fetch_from(M, search_bulk(M, days)).most_common() if not _is_protected(d)]
    total = 0
    plan = []
    for dom in targets:
        if _is_protected(dom):
            print("skip (protected): %s" % dom); continue
        n = len(search_sender(M, dom, days))
        plan.append((dom, n)); total += n
    for dom, n in plan:
        print("  %-34s %d msgs" % (dom, n))
    print("TOTAL to move to %s: %d messages from %d senders" % (M._trash, total, len(plan)))
    if not yes:
        print("\nDRY RUN. Re-run with --yes to move them to Trash (recoverable)."); M.logout(); return
    M.logout()
    M = connect(provider, addr, pw, readonly=False)
    moved = 0
    for dom, _ in plan:
        uids = search_sender(M, dom, days)
        moved += move_to_trash(M, uids)
        print("  moved %s (%d)" % (dom, len(uids)))
    print("DONE. Moved %d messages to %s (30-day recovery)." % (moved, M._trash))
    M.logout()


def cmd_unsub_run(M, domains, addr, pw):
    try:
        import requests
    except ImportError:
        sys.exit("unsub-run needs 'requests' (pip install requests).")
    smtp = None
    for dom in [x.strip() for x in domains.split(",") if x.strip()]:
        meth, tgt = unsub_method(M, dom)
        try:
            if meth == '1click':
                r = requests.post(tgt, data='List-Unsubscribe=One-Click',
                                  headers={'Content-Type': 'application/x-www-form-urlencoded',
                                           'User-Agent': 'Mozilla/5.0'}, timeout=20)
                print("%-30s 1click  HTTP %s" % (dom, r.status_code))
            elif meth == 'mailto':
                m = re.match(r'mailto:([^?]+)(\?(.*))?', tgt); to = m.group(1); subj = ''
                for kv in (m.group(3) or '').split('&'):
                    if kv.lower().startswith('subject='):
                        subj = unquote(kv[8:])
                if smtp is None:
                    smtp = smtplib.SMTP(PROVIDERS[M._prov]["smtp"], 587)
                    smtp.starttls(); smtp.login(addr, pw)
                msg = MIMEText(''); msg['From'] = addr; msg['To'] = to; msg['Subject'] = subj or 'unsubscribe'
                smtp.sendmail(addr, [to], msg.as_string())
                print("%-30s mailto  sent→%s" % (dom, to[:30]))
            elif meth == 'weblink':
                print("%-30s weblink (open manually, trusted only): %s" % (dom, tgt[:50]))
            else:
                print("%-30s no unsubscribe header" % dom)
        except Exception as e:
            print("%-30s ERR %s" % (dom, str(e)[:40]))
    if smtp:
        smtp.quit()


def cmd_wizard(provider):
    print("\n== mail-declutter (%s) ==" % provider)
    print("Safe by design: nothing is deleted permanently — mail is moved to Trash,")
    print("which you can restore for ~30 days. Read RULESET.md for the full policy.\n")
    addr, pw = ensure_creds(provider, interactive=True)
    M = connect(provider, addr, pw, readonly=True)
    print("\nConnected as %s. Scanning...\n" % addr)
    cmd_counts(M)
    print("\nTop bulk senders (old mail with an unsubscribe link):\n")
    dom = fetch_from(M, search_bulk(M))
    junk = [(d, c) for d, c in dom.most_common(40) if not _is_protected(d)]
    for d, c in junk[:25]:
        print("  %-34s %d" % (d, c))
    M.logout()
    if not junk:
        print("\nNothing obvious to clean. Done."); return
    picked = input("\nMove OLD mail from ALL these senders to Trash? (recoverable) [y/N] ").strip().lower()
    if picked == "y":
        cmd_sweep(provider, addr, pw, ",".join(d for d, _ in junk), 365, yes=False)
        if input("\nProceed for real? [y/N] ").strip().lower() == "y":
            cmd_sweep(provider, addr, pw, ",".join(d for d, _ in junk), 365, yes=True)
    if input("\nAlso UNSUBSCRIBE from these senders? [y/N] ").strip().lower() == "y":
        M = connect(provider, addr, pw, readonly=True)
        cmd_unsub_run(M, ",".join(d for d, _ in junk), addr, pw)
        M.logout()
    print("\nTip: after checking Trash looks right, empty it in your webmail. Re-run quarterly.")


# ------------------------------------------------------------------- main ------
def main():
    p = argparse.ArgumentParser(prog="mail-declutter", description=__doc__.splitlines()[0])
    p.add_argument("--provider", choices=list(PROVIDERS), default="gmail")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("wizard", help="guided end-to-end cleanup (start here)")
    sub.add_parser("setup", help="store credentials for a provider")
    sub.add_parser("counts")
    x = sub.add_parser("profile"); x.add_argument("--top", type=int, default=30)
    x = sub.add_parser("unsub-list"); x.add_argument("--top", type=int, default=40)
    x = sub.add_parser("sweep")
    x.add_argument("--senders", help="comma-separated domains; omit to target all non-protected bulk senders")
    x.add_argument("--days", type=int, default=365); x.add_argument("--yes", action="store_true")
    x = sub.add_parser("unsub-run"); x.add_argument("--domains", required=True)
    a = p.parse_args()
    prov = a.provider

    if a.cmd == "setup":
        run_setup(prov); return
    if a.cmd == "wizard":
        cmd_wizard(prov); return
    if a.cmd == "sweep":
        addr, pw = ensure_creds(prov, interactive=False)
        cmd_sweep(prov, addr, pw, a.senders, a.days, a.yes); return

    addr, pw = ensure_creds(prov, interactive=False)
    M = connect(prov, addr, pw, readonly=True)
    try:
        if a.cmd == "counts": cmd_counts(M)
        elif a.cmd == "profile": cmd_profile(M, a.top)
        elif a.cmd == "unsub-list": cmd_unsub_list(M, a.top)
        elif a.cmd == "unsub-run": cmd_unsub_run(M, a.domains, addr, pw)
    finally:
        try: M.logout()
        except Exception: pass


if __name__ == "__main__":
    main()
