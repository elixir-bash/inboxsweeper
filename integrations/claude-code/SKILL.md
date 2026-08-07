---
name: gmail-declutter
description: Clean up and unsubscribe from a personal Gmail over IMAP using an app password (macOS Keychain or env vars). Bulk-delete promotional/newsletter mail to Bin (30-day recovery, never permanent), profile noisy senders, and unsubscribe via RFC-8058 one-click or mailto. Use when the user wants to declutter Gmail, mass-delete promotions/updates, stop newsletters, or unsubscribe from mailing lists. Trigger words - gmail cleanup, declutter inbox, delete promotions, mass delete email, unsubscribe, newsletters, inbox zero.
---

# Gmail Declutter (skill)

Runs the `gmail_cleanup.py` CLI co-located in this skill folder. **Read `RULESET.md` (same
folder) before any delete or unsubscribe.**

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
python3 gmail_cleanup.py counts
python3 gmail_cleanup.py profile   --top 40
python3 gmail_cleanup.py unsub-list --top 40
python3 gmail_cleanup.py sweep     --query "<gmail query>"          # DRY RUN
python3 gmail_cleanup.py sweep     --query "<gmail query>" --yes    # → Bin
python3 gmail_cleanup.py unsub-run --domains "a.com,b.com"
```

## How to operate (follow RULESET.md)
1. `counts` → find the mass. `profile` → rank senders.
2. Classify senders PROTECT / DELETE / KEEP-BY-DEFAULT; confirm the DELETE set with the user.
3. `sweep` dry-run → show count → `--yes` to move to Bin (reversible). Verify a sample.
4. `unsub-list` → `unsub-run` recognized senders (one-click/mailto only).
5. Suspected spam / unrecognized → tell the user to **report spam**, do NOT unsubscribe.
6. Never permanent-delete. Never auto-click a `weblink` unsubscribe. Protect financial /
   security / government / transactional / personal / work senders.
7. Long runs: background them; surface a summary, not raw logs.
