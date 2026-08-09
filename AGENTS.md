# AGENTS.md — driving InboxSweeper from an AI coding agent

Instructions for **Codex, Jules, Cursor, Gemini CLI, Claude Code, or any AGENTS.md-aware /
tool-using agent** to operate this repo safely. (Claude Code can also install it as a skill —
see `integrations/claude-code/`.)

## What this is
A Python IMAP tool that cleans up and unsubscribes from a personal Gmail. `inboxsweeper.py`
is the entrypoint. Read the built-in safety rules before deleting, unsubscribing, or reporting spam.

## Credentials
Do NOT ask the user to paste their password into chat. Credentials come from:
- env vars `GMAIL_ADDR` + `GMAIL_APP_PASSWORD`, or
- macOS Keychain services `gmail_cleanup` (password) and `gmail_cleanup_addr`/account (address).

If missing, walk the user through creating a Gmail **app password**
(https://myaccount.google.com/apppasswords, requires 2-Step Verification) and storing it via
Keychain or env vars. The value must never appear in the transcript.

## Hard safety rules (do not violate)
1. **Never permanent-delete.** `sweep` only MOVEs to Trash (30-day recovery).
2. **Always dry-run first.** Run `sweep`/`spam` without `--yes`, show the count, get explicit
   approval, then re-run with `--yes`.
3. **Clean by sender, not by category.** Target `--senders`; never bulk-delete by date/label alone —
   transactional mail hides in "updates".
4. **Unsubscribe only recognized senders**, and only via `1click`/`mailto`. Never trigger a
   `weblink` unsubscribe automatically. For **unrecognized / suspected spam, use `spam --senders`**
   (reports to the Spam folder and trains the filter) — never unsubscribe from spam.
5. **Protect** financial, security, government, transactional, personal, and work senders — the
   engine shields these automatically and they can never be swept or reported. When a sender is
   ambiguous (community/religious/hobby), ask the user.

## Commands
```bash
python3 inboxsweeper.py wizard                              # guided: Clean up OR Report spam
python3 inboxsweeper.py counts                              # mailbox landscape
python3 inboxsweeper.py profile --top 40                    # rank noisy senders
python3 inboxsweeper.py unsub-list --top 40                 # unsubscribe method per sender
python3 inboxsweeper.py sweep --senders "a.com,b.com"       # DRY RUN, show count
python3 inboxsweeper.py sweep --senders "a.com,b.com" --yes # after approval → Trash
python3 inboxsweeper.py unsub-run --domains "a.com,b.com"   # one-click / mailto unsubscribe
python3 inboxsweeper.py spam  --senders "x.com" --yes       # report unrecognized senders as spam
```
Add `--provider yahoo` for Yahoo, and `--mode sloth|normal|madmax` to set how far back to reach
(default `normal` = older than 1 year).

## Recommended flow
1. `counts` → find the mass. `profile --top 40` → rank senders.
2. Classify senders **PROTECT / UNSUBSCRIBE / TRASH / REPORT-SPAM**; confirm the sets with the user.
3. Recognized senders: `unsub-run` first, then `sweep` (dry-run → `--yes`). Verify a sample in Trash.
4. Unrecognized / spammy senders: `spam --senders …` (dry-run → `--yes`) — do NOT unsubscribe.
5. Report what moved / unsubscribed / reported; note that transactional mail is unaffected.
6. Long operations: run in the background and surface a summary, not raw logs.
