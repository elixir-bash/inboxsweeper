# AGENTS.md — driving inboxsweeper from an AI coding agent

Instructions for Codex, Claude Code, or any tool-using agent to operate this repo safely.

## What this is
A Python IMAP tool that cleans up and unsubscribes from a personal Gmail. `inboxsweeper.py`
is the entrypoint. Read `RULESET.md` before deleting or unsubscribing anything.

## Credentials
Do NOT ask the user to paste their password into chat. Credentials come from:
- env vars `GMAIL_ADDR` + `GMAIL_APP_PASSWORD`, or
- macOS Keychain services `gmail_cleanup` (password) and `gmail_cleanup_addr`/account (address).

If missing, walk the user through creating a Gmail **app password**
(https://myaccount.google.com/apppasswords, requires 2-Step Verification) and storing it via
Keychain or env vars. The value must never appear in the transcript.

## Hard safety rules (do not violate)
1. **Never permanent-delete.** Only `sweep` (which MOVEs to Bin, 30-day recovery).
2. **Always dry-run first.** Run `sweep` without `--yes`, show the count, get explicit
   approval, then re-run with `--yes`.
3. **Clean by sender, not by category** — `category:updates` holds transactional mail.
4. **Unsubscribe only recognized senders**, and only via `1click`/`mailto`. Never trigger a
   `weblink` unsubscribe automatically, and never unsubscribe from suspected spam — advise
   "report spam" instead.
5. **Protect** financial, security, government, transactional, personal, and work senders
   (see `RULESET.md`). When a sender is ambiguous (community/religious/hobby), ask the user.

## Recommended flow
```bash
python3 inboxsweeper.py counts                       # landscape
python3 inboxsweeper.py profile --top 40             # rank noisy senders
python3 inboxsweeper.py sweep --query "<Q>"          # DRY RUN, show count
python3 inboxsweeper.py sweep --query "<Q>" --yes    # after approval → Bin
python3 inboxsweeper.py unsub-list --top 40          # methods per sender
python3 inboxsweeper.py unsub-run --domains "a.com,b.com"
```

## Presenting results
- After `profile`/`unsub-list`, group senders into PROTECT / DELETE / KEEP-BY-DEFAULT and let
  the user confirm the DELETE set before acting.
- Report what moved and what was unsubscribed; note that transactional mail is unaffected.
- Long operations: run in the background and surface a summary, not raw logs.
