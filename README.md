# gmail-declutter

Safe, scriptable Gmail cleanup **and** unsubscribe over IMAP — no Google Cloud project, no
OAuth consent screen, no browser extension. Just an app password.

- 🗑️ **Deletes to Bin, never permanently** (30-day recovery). Reversible by design.
- 🎯 **Cleans by sender, not by category** — because Gmail's "Updates" tab is full of
  *transactional* mail (receipts, orders, bookings) you don't want to lose.
- ✉️ **Unsubscribes** via the RFC-8058 one-click POST or `mailto` — the safe methods only.
- 🔒 **Safe by default** — protects financial, security, government, and transactional senders
  out of the box (see [`RULESET.md`](RULESET.md)).
- 🤖 **Drives from Claude Code or Codex** (see [Agent integration](#agent-integration)).

> ⚠️ **Read [`RULESET.md`](RULESET.md) before you run a sweep.** The one rule that matters
> most: **recognize a sender → unsubscribe; don't recognize it → report spam, never
> unsubscribe.** Clicking unsubscribe on real spam confirms your address is live and gets
> you *more* spam.

---

## 1. Prerequisites

- Python 3.9+
- `pip install -r requirements.txt` (only `requests`, and only for `unsub-run`)
- A Gmail account with **2-Step Verification ON** (required for app passwords)

## 2. Create a Gmail app password (step by step)

You never give this tool your real Google password. You create a scoped **app password**.

1. Turn on 2-Step Verification: **[myaccount.google.com/security](https://myaccount.google.com/security)**
   → *2-Step Verification* → follow the steps. (App passwords don't exist without it.)
2. Go to **[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)**.
3. App name: `gmail-declutter` → **Create**.
4. Google shows a **16-character** password like `abcd efgh ijkl mnop`. Copy it.
   (You can always revoke it later from that same page — the tool stops working instantly.)
5. IMAP is already enabled on modern Gmail (no toggle). If you have an old account:
   Gmail → ⚙️ *See all settings* → *Forwarding and POP/IMAP* → *Enable IMAP* → Save.

## 3. Store the credentials

**Option A — macOS Keychain (recommended on Mac).** The value is prompted and never echoed:

```bash
security add-generic-password -U -s gmail_cleanup      -a you@gmail.com -w   # paste app pw, hidden
security add-generic-password -U -s gmail_cleanup_addr -a account       -w you@gmail.com
```

**Option B — environment variables (any OS).** Put spaces-removed password here:

```bash
export GMAIL_ADDR="you@gmail.com"
export GMAIL_APP_PASSWORD="abcdefghijklmnop"
```

The tool checks env vars first, then Keychain.

## 4. Use it

```bash
# 1. See where the noise is
python3 gmail_cleanup.py counts

# 2. Rank the noisiest bulk senders (default query = the safe bulk set)
python3 gmail_cleanup.py profile --top 40

# 3. Preview a deletion (DRY RUN — nothing moves)
python3 gmail_cleanup.py sweep --query "older_than:1y unsubscribe from:linkedin.com"

# 4. Actually move them to Bin (30-day recovery)
python3 gmail_cleanup.py sweep --query "older_than:1y unsubscribe from:linkedin.com" --yes

# 5. See each sender's unsubscribe method, then unsubscribe from specific ones
python3 gmail_cleanup.py unsub-list --top 40
python3 gmail_cleanup.py unsub-run --domains "email-marriott.com,mail.zillow.com,uber.com"
```

### Commands

| Command | Purpose |
|---|---|
| `counts` | Landscape: promotions / social / updates / forums / safe-bulk-set sizes |
| `profile --query Q --top N` | Tally sender domains for a query |
| `unsub-list --query Q --top N` | Senders + unsubscribe method (`1click`/`mailto`/`weblink`/`none`) |
| `sweep --query Q [--batch 300] [--yes]` | Move matches to Bin. **Dry-run unless `--yes`.** |
| `unsub-run --domains a.com,b.com` | Execute unsubscribe (one-click POST or mailto/SMTP) |

The default `--query` everywhere is the **safe bulk set**: old mail that carries an
unsubscribe link, excluding starred/important, transactional keywords, and protected
senders. Widen or narrow it with any [Gmail search operators](https://support.google.com/mail/answer/7190).

## 5. Recommended flow

1. `counts` → find the mass (often it's `category:updates`, which hides receipts).
2. `profile` → rank bulk senders.
3. Classify each into **PROTECT / DELETE / KEEP-BY-DEFAULT** using [`RULESET.md`](RULESET.md).
4. `sweep` (dry-run → `--yes`) the DELETE set. Verify a sample in Gmail → Bin.
5. `unsub-list` → `unsub-run` the recognized DELETE senders.
6. Unrecognized/spammy senders: **report spam in Gmail — don't unsubscribe.**
7. Add Gmail **filters** for the worst repeat offenders so the backlog can't rebuild.

## How it works

- Connects over IMAP and searches with Gmail's `X-GM-RAW` extension, so any Gmail search
  query works server-side.
- "Delete" = IMAP `MOVE` to the Trash/Bin folder (auto-detected via the `\Trash` special-use
  flag), which is Gmail's 30-day-recoverable trash — not a permanent delete.
- Unsubscribe reads the message's `List-Unsubscribe` / `List-Unsubscribe-Post` headers:
  - **one-click** → HTTP `POST` with body `List-Unsubscribe=One-Click` ([RFC 8058](https://www.rfc-editor.org/rfc/rfc8058)).
  - **mailto** → sends an unsubscribe email via SMTP using your app password.
  - **weblink-only** → reported for manual handling (never auto-clicked; could be a tracker).

## Agent integration

This repo ships ready-made instructions so an AI coding agent can drive the tool for you.

- **Claude Code** — install as a skill (bundles the script + ruleset so it's self-contained):
  ```bash
  mkdir -p ~/.claude/skills/gmail-declutter
  cp integrations/claude-code/SKILL.md gmail_cleanup.py RULESET.md ~/.claude/skills/gmail-declutter/
  ```
  Then just ask Claude: *"declutter my gmail"* / *"unsubscribe from these senders"*.
- **Codex / other agents** — point the agent at [`AGENTS.md`](AGENTS.md) (or drop it at your
  repo root). It documents the commands, the safety rules, and the recommended flow.

## FAQ

**Will I still get receipts/order confirmations after unsubscribing?** Yes. Unsubscribing
only cancels a marketing list; transactional mail is a separate, CAN-SPAM-exempt stream.

**Is it safe?** Deletions go to Bin (recoverable). Unsubscribes use one-click/mailto only.
The tool never permanently deletes and never clicks arbitrary web links.

**Does it work with non-Gmail IMAP?** It's built for Gmail (uses `X-GM-RAW` and Gmail
categories). Other providers need query changes.

## Security

- Uses an **app password**, never your Google password. Revoke it anytime at
  [apppasswords](https://myaccount.google.com/apppasswords) and the tool dies instantly.
- Nothing is hardcoded; credentials come from Keychain or env vars.
- `.gitignore` keeps local credential files out of the repo.

## License

MIT — see [`LICENSE`](LICENSE). Personal tool; use at your own risk. Always dry-run first.
