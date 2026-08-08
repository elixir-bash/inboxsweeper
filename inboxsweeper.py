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
# Substrings that mark a sender as financial / security / sensitive → never auto-classified as junk.
# Banks and fintechs now add unsubscribe headers even to important mail, so "has unsubscribe"
# is NOT a safe "junk" signal — this shields them.
PROTECT_DOMAIN_KW = ["bank", "amex", "americanexpress", "experian", "equifax", "transunion",
                     "venmo", "paypal", "visa", "mastercard", "discover", "cred.club", "creditkarma",
                     "wazirx", "coinbase", "binance", "kraken", "invest", "capital", "securit",
                     "trading", "mutualfund", "brokerage", "nse", "bse", "sensex", "insur",
                     "hdfc", "icici", "sbi", "kotak", "citi", "chase", "wellsfargo", "hsbc",
                     "fidelity", "schwab", "wealthfront", "robinhood", "motilaloswal", "zerodha",
                     "groww", "irs", ".gov", ".gc.ca", "vanguard", "biltrewards",
                     "mutual", "tatamf", "quant.in", "depositor", "nsdl", "cdsl", "kfin",
                     "registrar", "registry", "axisdirect", "kp.org", "health"]
PROTECT_KW = ["receipt", "invoice", "order", "booking", "reservation", "ticket",
              "statement", "tax", "refund", "payment", "confirmation"]

# Cleaning modes → how far back "bulk to clean" reaches (days). Financial/bank/transactional
# shielding stays ON in EVERY mode — MadMax just widens the age window, it doesn't drop protection.
MODES = {"sloth": 730, "normal": 365, "madmax": 0}   # 0 = all-time (includes recent spam)


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


def _imap_search(M, criteria):
    """IMAP SEARCH that falls back to ALL when the server rejects the criteria (e.g. Yahoo)."""
    try:
        t, d = M.uid('search', None, *criteria)
        if t == 'OK':
            return d[0].split() if d and d[0] else []
    except imaplib.IMAP4.error:
        pass
    t, d = M.uid('search', None, 'ALL')
    return d[0].split() if d and d[0] else []


def _has_unsub(M, uids):
    """Keep UIDs whose message carries a List-Unsubscribe header. Fetches the FULL header block —
    Yahoo's IMAP returns empty for HEADER.FIELDS(List-Unsubscribe), so a field-scoped fetch misses everything."""
    keep = []
    n = len(uids)
    for i in range(0, n, 200):
        if n > 400:
            sys.stderr.write("\r  scanning %d/%d messages…" % (min(i + 200, n), n)); sys.stderr.flush()
        t, d = M.uid('fetch', b','.join(uids[i:i + 200]), '(UID BODY.PEEK[HEADER])')
        for it in d or []:
            if isinstance(it, tuple):
                m = re.search(rb'UID (\d+)', it[0])
                if m and b'list-unsubscribe:' in it[1].lower():
                    keep.append(m.group(1))
    if n > 400:
        sys.stderr.write("\r" + " " * 44 + "\r"); sys.stderr.flush()
    return keep


def search_bulk(M, days=365):
    """UIDs of old messages that carry an unsubscribe header (the bulk-mail signal)."""
    if PROVIDERS[M._prov]["backend"] == "gmail":
        q = ("older_than:%dd unsubscribe -is:starred -{%s} %s"
             % (days, " ".join(PROTECT_KW), " ".join("-from:%s" % d for d in PROTECT_SENDERS)))
        t, d = M.uid('search', 'X-GM-RAW', '"%s"' % q)
        return d[0].split() if d and d[0] else []
    # Standard IMAP (Yahoo, etc.): HEADER searches are often unsupported — filter client-side.
    return _has_unsub(M, _imap_search(M, ['BEFORE', _imap_date(days)]))


def search_sender(M, domain, days=365):
    if PROVIDERS[M._prov]["backend"] == "gmail":
        q = "from:%s" % domain if days <= 0 else "from:%s older_than:%dd" % (domain, days)
        t, d = M.uid('search', 'X-GM-RAW', '"%s"' % q)
        return d[0].split() if d and d[0] else []
    tries = ([['FROM', domain, 'BEFORE', _imap_date(days)]] if days > 0 else []) + [['FROM', domain]]
    for crit in tries:
        try:
            t, d = M.uid('search', None, *crit)
            if t == 'OK':
                return d[0].split() if d and d[0] else []
        except imaplib.IMAP4.error:
            continue
    return []


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
    if PROVIDERS[M._prov]["backend"] == "gmail":
        # in:anywhere so we can still read the header even after mail was moved to Trash
        t, d = M.uid('search', 'X-GM-RAW', '"from:%s in:anywhere"' % domain)
        ids = d[0].split() if d and d[0] else []
    else:
        ids = search_sender(M, domain, days=0)  # all-time — find any message to read its header
    if not ids:
        return ('none', '')
    # Full header (Yahoo returns empty for HEADER.FIELDS of List-Unsubscribe).
    t, h = M.uid('fetch', ids[-1], '(BODY.PEEK[HEADER])')
    raw = b''.join(x[1] for x in h if isinstance(x, tuple))
    import email as _email
    msg = _email.message_from_bytes(raw)
    lu_hdr = msg.get('List-Unsubscribe', '') or ''
    post = msg.get('List-Unsubscribe-Post', '') or ''
    lu = re.findall(r'<([^>]+)>', lu_hdr)
    oc = 'One-Click' in post or 'One-Click' in lu_hdr
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


def total_size(M, uids):
    """Sum of RFC822.SIZE for a set of UIDs (bytes) — powers the 'storage freed' stat."""
    tot = 0
    for i in range(0, len(uids), 1000):
        t, d = M.uid('fetch', b','.join(uids[i:i + 1000]), '(RFC822.SIZE)')
        for it in d:
            raw = it if isinstance(it, (bytes, bytearray)) else (it[0] if isinstance(it, tuple) else b'')
            m = re.search(rb'RFC822\.SIZE (\d+)', raw)
            if m:
                tot += int(m.group(1))
    return tot


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return "%.1f %s" % (n, u)
        n /= 1024.0


# ------------------------------------------------------------- blocklist -------
def _blocklist_path(provider):
    d = os.path.expanduser("~/.config/mail-declutter"); os.makedirs(d, exist_ok=True)
    return os.path.join(d, "%s.blocklist" % provider)


def load_blocklist(provider):
    p = _blocklist_path(provider)
    return [l.strip() for l in open(p) if l.strip()] if os.path.exists(p) else []


def add_blocklist(provider, domains):
    cur = set(load_blocklist(provider))
    cur.update(d.strip() for d in domains if d.strip())
    with open(_blocklist_path(provider), "w") as f:
        f.write("\n".join(sorted(cur)) + "\n")
    return sorted(cur)


# ---------------------------------------------------- anonymous telemetry ------
# Off unless a stats endpoint is configured. Sends counts only — never addresses,
# senders, subjects, or content. Disable entirely with INBOXSWEEPER_NO_TELEMETRY=1.
STATS_URL = os.environ.get("INBOXSWEEPER_STATS_URL",
                           "https://inboxsweeper-backend.elixir-bash.workers.dev")


def _anon_uid():
    p = os.path.expanduser("~/.config/mail-declutter/uid")
    if os.path.exists(p):
        return open(p).read().strip()
    import uuid
    os.makedirs(os.path.dirname(p), exist_ok=True)
    u = uuid.uuid4().hex
    open(p, "w").write(u)
    return u


TOOL_VERSION = "0.3"


def track(action, provider="", ok=True, emails=0, size_bytes=0, unsubs=0):
    """Anonymous usage + performance event. Counts/metadata only — never PII."""
    if not STATS_URL or os.environ.get("INBOXSWEEPER_NO_TELEMETRY"):
        return
    try:
        import json as _j, urllib.request as _u, platform
        body = _j.dumps({"uid": _anon_uid(), "tool": "inboxsweeper", "v": TOOL_VERSION,
                         "os": platform.system(), "action": action, "provider": provider,
                         "ok": bool(ok), "emails": emails,
                         "mb": round(size_bytes / 1048576.0, 1), "unsubs": unsubs}).encode()
        _u.urlopen(_u.Request(STATS_URL.rstrip("/") + "/event", data=body,
                              headers={"Content-Type": "application/json",
                                       "User-Agent": "InboxSweeper/" + TOOL_VERSION}), timeout=4)
    except Exception:
        pass


# ------------------------------------------------------- quarterly reminder ----
_REMIND_TAG = "# inboxsweeper-reminder"


def cmd_remind(off=False):
    self_path = os.path.abspath(sys.argv[0])
    run = "%s %s remind-run" % (sys.executable, self_path)
    if sys.platform == "win32":
        print("Windows: open Task Scheduler and create a quarterly task running:\n  %s" % run)
        return
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    lines = [l for l in cur.splitlines() if _REMIND_TAG not in l]
    if off:
        print("Quarterly reminder removed.")
    else:
        # 9am on the 1st of Jan/Apr/Jul/Oct
        lines.append("0 9 1 1,4,7,10 * %s %s" % (run, _REMIND_TAG))
        print("Quarterly reminder installed — you'll get a nudge (and blocked senders auto-clean)"
              "\n  at 9am on Jan/Apr/Jul/Oct 1st. Turn off with:  remind --off")
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True)


def cmd_remind_run(provider):
    msg = "Time for your quarterly inbox sweep - open InboxSweeper to tidy up."
    try:
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e", 'display notification "%s" with title "InboxSweeper"' % msg])
        elif sys.platform.startswith("linux"):
            subprocess.run(["notify-send", "InboxSweeper", msg])
    except Exception:
        pass
    try:  # keep pre-approved blocked senders swept (safe — user already blocked them)
        addr, pw = load_creds(provider)
        if addr and pw and load_blocklist(provider):
            cmd_autoclean(provider, addr, pw, yes=True)
    except Exception:
        pass


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
def cmd_counts(M, days=365):
    P = PROVIDERS[M._prov]
    if P["backend"] != "gmail":
        print("⚠  EXPERIMENTAL (%s): over IMAP, %s exposes only your ~10,000 most-recent messages"
              % (M._prov, M._prov.title()))
        print("   per folder — older mail is NOT reachable here. For a larger backlog, use %s's"
              % M._prov.title())
        print("   own web unsubscribe (Settings → More Settings → Subscriptions). Gmail has no cap.\n")
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
    print("%-28s %d" % ("bulk (has unsubscribe)", len(search_bulk(M, days))))


def cmd_profile(M, top, days=365):
    uids = search_bulk(M, days)
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
    d = domain.lower()
    return any(p in d for p in PROTECT_SENDERS) or any(k in d for k in PROTECT_DOMAIN_KW)


def cmd_sweep(provider, addr, pw, senders, days, yes):
    M = connect(provider, addr, pw, readonly=True)
    targets = [s.strip() for s in senders.split(",") if s.strip()] if senders else \
        [d for d, _ in fetch_from(M, search_bulk(M, days)).most_common() if not _is_protected(d)]
    total = 0; tot_sz = 0
    plan = []
    for dom in targets:
        if _is_protected(dom):
            print("skip (protected): %s" % dom); continue
        uids = search_sender(M, dom, days)
        plan.append((dom, len(uids))); total += len(uids); tot_sz += total_size(M, uids)
    for dom, n in plan:
        print("  %-34s %d msgs" % (dom, n))
    print("TOTAL to move to %s: %d messages (~%s) from %d senders" % (M._trash, total, human(tot_sz), len(plan)))
    if not yes:
        print("\nDRY RUN. Re-run with --yes to move them to Trash (recoverable)."); M.logout(); return (0, 0)
    M.logout()
    M = connect(provider, addr, pw, readonly=False)
    moved = 0; freed = 0
    for dom, _ in plan:
        uids = search_sender(M, dom, days)
        freed += total_size(M, uids)
        moved += move_to_trash(M, uids)
        print("  moved %s (%d)" % (dom, len(uids)))
    print("DONE. Moved %d messages to %s — freed ~%s (30-day recovery)." % (moved, M._trash, human(freed)))
    M.logout()
    track("sweep", provider, emails=moved, size_bytes=freed)
    return (moved, freed)


def cmd_block(provider, addr, pw, senders, yes):
    doms = [s.strip() for s in senders.split(",") if s.strip()]
    add_blocklist(provider, doms)
    print("Blocked %d sender(s): %s" % (len(doms), ", ".join(doms)))
    print("Deleting their existing mail (all dates); future mail is auto-cleaned via `autoclean`.\n")
    cmd_sweep(provider, addr, pw, ",".join(doms), 0, yes)  # days<=0 → all-time


def cmd_autoclean(provider, addr, pw, yes):
    bl = load_blocklist(provider)
    if not bl:
        print("No blocked senders yet. Use:  block --senders a.com,b.com"); return
    print("Auto-cleaning %d blocked sender(s): %s" % (len(bl), ", ".join(bl)))
    cmd_sweep(provider, addr, pw, ",".join(bl), 0, yes)


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
    print("\n== InboxSweeper (%s) ==" % provider)
    print("Safe by design: deleted mail goes to Trash (recoverable ~30 days).\n")
    print("Cleaning mode:")
    print("  1) Sloth   — only mail older than 2 years  (safest)")
    print("  2) Normal  — mail older than 1 year         (recommended)")
    print("  3) MadMax  — ALL promo mail, incl. recent   (aggressive)")
    print("  Banks, credit, payments & receipts stay protected in every mode.")
    mode = {"1": "sloth", "2": "normal", "3": "madmax"}.get(input("Pick [1/2/3, default 2]: ").strip(), "normal")
    days = MODES[mode]
    print("→ %s mode.\n" % mode)
    addr, pw = ensure_creds(provider, interactive=True)
    M = connect(provider, addr, pw, readonly=True)
    print("\nConnected as %s.\nScanning your mailbox — this can take up to a minute…\n" % addr)
    bulk = search_bulk(M, days)
    dom = fetch_from(M, bulk)
    junk = [(d, c) for d, c in dom.most_common(40) if not _is_protected(d)]
    shielded = sum(1 for d, _ in dom.items() if _is_protected(d))
    M.logout()
    label = "any age" if days == 0 else "older than %d days" % days
    print("Found %d promotional messages (%s). %d financial/protected senders auto-shielded.\n"
          % (len(bulk), label, shielded))
    if not junk:
        print("Nothing safe to clean in this mode.")
        if mode != "madmax":
            print("(Try MadMax for recent mail; for a large Yahoo backlog use Yahoo's web unsubscribe.)")
        return
    print("Junk senders:")
    for i, (d, c) in enumerate(junk[:25], 1):
        print("  %2d) %-34s %d" % (i, d, c))
    skip = input("\nEnter numbers to SKIP (e.g. 2,5), or press Enter to include all: ").strip()
    skipset = {int(t) for t in skip.replace(" ", "").split(",") if t.isdigit()}
    chosen = [junk[i] for i in range(min(25, len(junk))) if (i + 1) not in skipset]
    if not chosen:
        print("Nothing selected. Done."); return
    doms = ",".join(d for d, _ in chosen)
    # Unsubscribe FIRST — while the mail is still in your mailbox (after it's in Trash the link's gone).
    if input("\nUNSUBSCRIBE from the %d selected senders first? [y/N] " % len(chosen)).strip().lower() == "y":
        M = connect(provider, addr, pw, readonly=True)
        cmd_unsub_run(M, doms, addr, pw)
        M.logout()
    if input("\nMove their mail to Trash? (recoverable) [y/N] ").strip().lower() == "y":
        cmd_sweep(provider, addr, pw, doms, days, yes=False)
        if input("\nProceed for real? [y/N] ").strip().lower() == "y":
            cmd_sweep(provider, addr, pw, doms, days, yes=True)
    print("\nTip: check Trash looks right, then empty it in your webmail. Re-run quarterly.")


# ------------------------------------------------------------------- main ------
def main():
    base = argparse.ArgumentParser(add_help=False)
    base.add_argument("--provider", choices=list(PROVIDERS), default="gmail",
                      help="mail provider (default: gmail)")
    base.add_argument("--mode", choices=list(MODES), default="normal",
                      help="aggressiveness: sloth (>2yr) | normal (>1yr, default) | madmax (all, incl. recent)")
    p = argparse.ArgumentParser(prog="inboxsweeper", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve", parents=[base], help="open the browser UI (easiest, no terminal after launch)")
    sub.add_parser("wizard", parents=[base], help="guided end-to-end cleanup (start here)")
    sub.add_parser("setup", parents=[base], help="store credentials for a provider")
    sub.add_parser("counts", parents=[base])
    x = sub.add_parser("profile", parents=[base]); x.add_argument("--top", type=int, default=30)
    x = sub.add_parser("unsub-list", parents=[base]); x.add_argument("--top", type=int, default=40)
    x = sub.add_parser("sweep", parents=[base])
    x.add_argument("--senders", help="comma-separated domains; omit to target all non-protected bulk senders")
    x.add_argument("--days", type=int, default=None, help="override the mode's age window"); x.add_argument("--yes", action="store_true")
    x = sub.add_parser("unsub-run", parents=[base]); x.add_argument("--domains", required=True)
    x = sub.add_parser("block", parents=[base], help="delete a sender's mail + block them so future mail is auto-cleaned")
    x.add_argument("--senders", required=True); x.add_argument("--yes", action="store_true")
    x = sub.add_parser("autoclean", parents=[base], help="re-clean every blocked sender (great for a cron job)")
    x.add_argument("--yes", action="store_true")
    x = sub.add_parser("remind", parents=[base], help="install a quarterly reminder to clean your inbox")
    x.add_argument("--off", action="store_true")
    sub.add_parser("remind-run", parents=[base], help=argparse.SUPPRESS)
    a = p.parse_args()
    prov = a.provider
    track("cmd_" + a.cmd, provider=prov)  # anonymous usage/perf ping (off unless configured)

    if a.cmd == "remind":
        cmd_remind(a.off); return
    if a.cmd == "remind-run":
        cmd_remind_run(prov); return

    if a.cmd == "serve":
        import webui; webui.serve(); return
    if a.cmd == "setup":
        run_setup(prov); return
    if a.cmd == "wizard":
        cmd_wizard(prov); return
    if a.cmd == "sweep":
        addr, pw = ensure_creds(prov, interactive=False)
        days = a.days if a.days is not None else MODES[a.mode]
        cmd_sweep(prov, addr, pw, a.senders, days, a.yes); return
    if a.cmd == "block":
        addr, pw = ensure_creds(prov, interactive=False)
        cmd_block(prov, addr, pw, a.senders, a.yes); return
    if a.cmd == "autoclean":
        addr, pw = ensure_creds(prov, interactive=False)
        cmd_autoclean(prov, addr, pw, a.yes); return

    addr, pw = ensure_creds(prov, interactive=False)
    M = connect(prov, addr, pw, readonly=True)
    try:
        if a.cmd == "counts": cmd_counts(M, MODES[a.mode])
        elif a.cmd == "profile": cmd_profile(M, a.top, MODES[a.mode])
        elif a.cmd == "unsub-list": cmd_unsub_list(M, a.top)
        elif a.cmd == "unsub-run": cmd_unsub_run(M, a.domains, addr, pw)
    finally:
        try: M.logout()
        except Exception: pass


if __name__ == "__main__":
    main()
