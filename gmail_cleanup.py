#!/usr/bin/env python3
"""gmail-declutter — safe Gmail cleanup + unsubscribe over IMAP.

No Gmail API/CLI/OAuth project needed — just an app password. Uses Gmail's X-GM-RAW
so full Gmail search syntax works (category:promotions, older_than:1y, from:, ...).
Deletions MOVE to Bin/Trash (30-day recovery) — never permanent. Unsubscribes use the
RFC-8058 one-click POST or a mailto (sent via SMTP).

Credentials (resolved in this order):
  1. env vars   GMAIL_ADDR + GMAIL_APP_PASSWORD
  2. macOS Keychain:  service "gmail_cleanup" (password) + "gmail_cleanup_addr"/account (address)

Never use your real Google password — create an app password (see README).

Commands:
  counts                                  landscape (promotions/social/updates/…)
  profile    [--query Q] [--top N]        sender-domain tally for a query
  unsub-list [--query Q] [--top N]        senders + unsubscribe method
  sweep      --query Q [--batch 300] [--yes]   move matches to Bin (dry-run unless --yes)
  unsub-run  --domains a.com,b.com        execute unsubscribe (one-click / mailto)
"""
import argparse, imaplib, os, re, subprocess, sys, time, smtplib
from collections import Counter
from email.mime.text import MIMEText
from urllib.parse import unquote

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"

# --- safety defaults: protect transactional / sensitive senders + keywords -----------
PROTECT_SENDERS = ["google.com", "gmail.com", "amazon.com", "amazon.in", "github.com",
                   "apple.com", "microsoft.com", "paypal.com", "gov.in", "nic.in"]
PROTECT_KEYWORDS = ("receipt invoice order booking reservation ticket statement tax "
                    "refund payment confirmation")
SAFE_BULK = ("older_than:1y unsubscribe -is:important -is:starred -{%s} %s"
             % (PROTECT_KEYWORDS, " ".join("-from:%s" % d for d in PROTECT_SENDERS)))


# --- credentials ---------------------------------------------------------------------
def _keychain(service, account):
    if sys.platform != "darwin":
        return ""
    try:
        return subprocess.run(["security", "find-generic-password", "-s", service,
                               "-a", account, "-w"], capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""


def creds():
    addr = os.environ.get("GMAIL_ADDR") or _keychain("gmail_cleanup_addr", "account")
    pw = os.environ.get("GMAIL_APP_PASSWORD") or (_keychain("gmail_cleanup", addr) if addr else "")
    if not addr or not pw:
        sys.exit("No credentials found.\n"
                 "  Set env GMAIL_ADDR + GMAIL_APP_PASSWORD, or store in macOS Keychain:\n"
                 "    security add-generic-password -U -s gmail_cleanup -a you@gmail.com -w\n"
                 "    security add-generic-password -U -s gmail_cleanup_addr -a account -w you@gmail.com\n"
                 "  Create an app password at https://myaccount.google.com/apppasswords")
    return addr, pw.replace(" ", "")


# --- imap helpers --------------------------------------------------------------------
def _detect_folders(M):
    """Return (all_mail, trash) folder names via special-use attributes; fall back to guesses."""
    allm = trash = None
    typ, boxes = M.list()
    for b in boxes or []:
        s = b.decode(errors="ignore")
        name = s.split(' "/" ')[-1].strip().strip('"') if ' "/" ' in s else s.split(' "." ')[-1].strip().strip('"')
        if "\\All" in s:
            allm = name
        if "\\Trash" in s:
            trash = name
    return (allm or "[Gmail]/All Mail"), (trash or "[Gmail]/Trash")


def connect(addr, pw, readonly=True):
    M = imaplib.IMAP4_SSL(IMAP_HOST)
    M.login(addr, pw)
    allm, trash = _detect_folders(M)
    M._allmail, M._trash = allm, trash
    M.select('"%s"' % allm, readonly=readonly)
    return M


def raw_uids(M, q):
    typ, d = M.uid('search', 'X-GM-RAW', '"%s"' % q)
    return d[0].split() if d and d[0] else []


def domain_tally(M, uids):
    dom = Counter()
    for i in range(0, len(uids), 400):
        typ, fd = M.uid('fetch', b','.join(uids[i:i + 400]), '(BODY.PEEK[HEADER.FIELDS (FROM)])')
        for it in fd:
            if isinstance(it, tuple):
                raw = it[1].decode('utf-8', 'ignore')
                m = re.search(r'<([^>]+)>', raw) or re.search(r'([\w.\-+]+@[\w.\-]+)', raw)
                if m:
                    dom[m.group(1).split('@')[-1].lower()] += 1
    return dom


def unsub_method(M, domain):
    ids = raw_uids(M, 'from:%s unsubscribe newer_than:3y' % domain)
    if not ids:
        return ('none', '')
    typ, h = M.uid('fetch', ids[-1], '(BODY.PEEK[HEADER.FIELDS (List-Unsubscribe List-Unsubscribe-Post)])')
    hdr = ''.join(x[1].decode('utf-8', 'ignore') for x in h if isinstance(x, tuple))
    lu = re.findall(r'<([^>]+)>', hdr)
    oneclick = 'One-Click' in hdr
    https = [u for u in lu if u.startswith('http')]
    mailto = [u for u in lu if u.startswith('mailto')]
    if https and oneclick:
        return ('1click', https[0])
    if mailto:
        return ('mailto', mailto[0])
    if https:
        return ('weblink', https[0])
    return ('none', '')


# --- commands ------------------------------------------------------------------------
def cmd_counts(M, a):
    for q, label in [("category:promotions", "promotions"),
                     ("category:social older_than:1y", "social >1y"),
                     ("category:updates", "updates (holds receipts!)"),
                     ("category:forums", "forums"),
                     (SAFE_BULK, "SAFE bulk-delete set")]:
        print("%-28s %d" % (label, len(raw_uids(M, q))))


def cmd_profile(M, a):
    uids = raw_uids(M, a.query)
    dom = domain_tally(M, uids)
    print("matches: %d   distinct senders: %d\n" % (len(uids), len(dom)))
    for d, c in dom.most_common(a.top):
        print("%-34s %d" % (d, c))


def cmd_unsub_list(M, a):
    uids = raw_uids(M, a.query)
    dom = domain_tally(M, uids)
    print("%-34s %5s  %s" % ("SENDER", "#MSG", "METHOD"))
    print("-" * 54)
    for d, c in dom.most_common(a.top):
        meth, _ = unsub_method(M, d)
        print("%-34s %5d  %s" % (d, c, meth))


def cmd_sweep(M, a, addr, pw):
    uids = raw_uids(M, a.query)
    print("query matches: %d  → %s" % (len(uids), M._trash))
    if not a.yes:
        print("DRY RUN. Re-run with --yes to move them to Bin (30-day recovery).")
        return
    M = connect(addr, pw, readonly=False)
    moved = 0
    for _ in range(1, 300):
        try:
            M.select('"%s"' % M._allmail)
            ids = raw_uids(M, a.query)
            if not ids:
                print("done — none left.")
                break
            batch = ids[:a.batch]
            M.uid('MOVE', b','.join(batch), '"%s"' % M._trash)
            moved += len(batch)
            print("moved %d (total %d, %d remaining)" % (len(batch), moved, len(ids) - len(batch)))
            time.sleep(1.5)
        except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError) as e:
            print("  reconnect after: %s" % str(e)[:50])
            time.sleep(4)
            try:
                M.logout()
            except Exception:
                pass
            M = connect(addr, pw, readonly=False)
    print("TOTAL moved to Bin:", moved)


def cmd_unsub_run(M, a, addr, pw):
    try:
        import requests
    except ImportError:
        sys.exit("unsub-run needs 'requests' (pip install requests).")
    smtp = None
    for dom in [x.strip() for x in a.domains.split(",") if x.strip()]:
        meth, tgt = unsub_method(M, dom)
        try:
            if meth == '1click':
                r = requests.post(tgt, data='List-Unsubscribe=One-Click',
                                  headers={'Content-Type': 'application/x-www-form-urlencoded',
                                           'User-Agent': 'Mozilla/5.0'}, timeout=20)
                print("%-30s 1click  HTTP %s" % (dom, r.status_code))
            elif meth == 'mailto':
                m = re.match(r'mailto:([^?]+)(\?(.*))?', tgt)
                to = m.group(1)
                subj = ''
                for kv in (m.group(3) or '').split('&'):
                    if kv.lower().startswith('subject='):
                        subj = unquote(kv[8:])
                if smtp is None:
                    smtp = smtplib.SMTP(SMTP_HOST, 587)
                    smtp.starttls()
                    smtp.login(addr, pw)
                msg = MIMEText('')
                msg['From'] = addr
                msg['To'] = to
                msg['Subject'] = subj or 'unsubscribe'
                smtp.sendmail(addr, [to], msg.as_string())
                print("%-30s mailto  sent→%s" % (dom, to[:30]))
            elif meth == 'weblink':
                print("%-30s weblink (open manually — trusted senders only): %s" % (dom, tgt[:54]))
            else:
                print("%-30s no unsubscribe header found" % dom)
        except Exception as e:
            print("%-30s ERR %s" % (dom, str(e)[:40]))
    if smtp:
        smtp.quit()


def main():
    p = argparse.ArgumentParser(prog="gmail_cleanup.py",
                                description="Safe Gmail cleanup + unsubscribe over IMAP.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("counts")
    x = sub.add_parser("profile"); x.add_argument("--query", default=SAFE_BULK); x.add_argument("--top", type=int, default=30)
    x = sub.add_parser("unsub-list"); x.add_argument("--query", default=SAFE_BULK); x.add_argument("--top", type=int, default=40)
    x = sub.add_parser("sweep"); x.add_argument("--query", default=SAFE_BULK); x.add_argument("--batch", type=int, default=300); x.add_argument("--yes", action="store_true")
    x = sub.add_parser("unsub-run"); x.add_argument("--domains", required=True)
    a = p.parse_args()

    addr, pw = creds()
    ro = a.cmd in ("counts", "profile", "unsub-list")
    M = connect(addr, pw, readonly=ro)
    try:
        {"counts": lambda: cmd_counts(M, a),
         "profile": lambda: cmd_profile(M, a),
         "unsub-list": lambda: cmd_unsub_list(M, a),
         "sweep": lambda: cmd_sweep(M, a, addr, pw),
         "unsub-run": lambda: cmd_unsub_run(M, a, addr, pw)}[a.cmd]()
    finally:
        try:
            M.logout()
        except Exception:
            pass


if __name__ == "__main__":
    main()
