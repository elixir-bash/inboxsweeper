---
name: inboxsweeper
description: Clean up, unsubscribe from, and report spam in a personal Gmail or Yahoo/IMAP mailbox using an app password (macOS Keychain or env vars). Bulk-delete promotional/newsletter mail to Trash (30-day recovery, never permanent), profile noisy senders, unsubscribe via RFC-8058 one-click or mailto, and report unrecognized senders as spam (trains the filter). Runs 100% locally; nothing is uploaded. Use when the user wants to declutter Gmail/Yahoo, mass-delete promotions/updates, stop newsletters, unsubscribe from mailing lists, or flag spam. Trigger words - gmail cleanup, yahoo cleanup, declutter inbox, delete promotions, mass delete email, unsubscribe, report spam, newsletters, inbox zero.
---

# InboxSweeper (skill)

Runs the `inboxsweeper.py` CLI co-located in this skill folder. **Follow the safety rules below
before any delete, unsubscribe, or spam report** — the tool also auto-shields financial/security/
government senders so they can never be touched.

## Setup (one time)
1. Gmail account with 2-Step Verification ON → create an app password at
   https://myaccount.google.com/apppasswords.
2. Store creds (macOS): the value is prompted, never echoed —
   ```
   security add-generic-password -U -s gmail_cleanup -a you@gmail.com -w
   security add-generic-password -U -s gmail_cleanup_addr -a account -w you@gmail.com
   ```
   Or set `GMAIL_ADDR` + `GMAIL_APP_PASSWORD` env vars.

## Commands
```
python3 inboxsweeper.py wizard                              # guided: Clean up OR Report spam
python3 inboxsweeper.py counts
python3 inboxsweeper.py profile    --top 40
python3 inboxsweeper.py unsub-list --top 40
python3 inboxsweeper.py sweep     --senders "a.com,b.com"          # DRY RUN
python3 inboxsweeper.py sweep     --senders "a.com,b.com" --yes    # → Trash
python3 inboxsweeper.py unsub-run --domains "a.com,b.com"
python3 inboxsweeper.py spam      --senders "x.com" --yes          # report unrecognized as spam
```
Add `--provider yahoo` for Yahoo, and `--mode sloth|normal|madmax` to set how far back to reach.

## How to operate (follow the built-in safety rules)
1. `counts` → find the mass. `profile` → rank senders.
2. Classify senders PROTECT / UNSUBSCRIBE / TRASH / REPORT-SPAM; confirm the sets with the user.
3. Recognized senders: `unsub-run` first, then `sweep` dry-run → `--yes` to move to Trash. Verify a sample.
4. Unrecognized / suspected spam → `spam --senders …` (dry-run → `--yes`); do NOT unsubscribe.
5. Never permanent-delete. Never auto-click a `weblink` unsubscribe. Protect financial /
   security / government / transactional / personal / work senders (shielded automatically).
6. Long runs: background them; surface a summary, not raw logs.
