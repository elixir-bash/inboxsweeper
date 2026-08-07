# gmail-declutter

Safe inbox cleanup **and** unsubscribe for **Gmail and Yahoo** over IMAP — no API project, no
OAuth consent screen, no browser extension. Just an app password. Run it with one guided
command; no coding and no AI agent required.

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

## 🖱️ Easiest: the app (no terminal)

Prefer clicking to typing? After a one-time `pip install -r requirements.txt`:

- **macOS:** double-click **`Declutter.command`**
- **Windows:** double-click **`Declutter.bat`**

It opens a small app in your browser: pick Gmail or Yahoo, paste an app password once, hit
**Scan**, then tick the senders you want gone and click **Move to Trash** or **Unsubscribe**.
Everything runs locally on your machine (nothing is uploaded anywhere), and deletions go to
Trash so they're recoverable. (Prefer the command line? `python3 gmail_cleanup.py serve` does
the same thing.)

> Standalone signed `.app` / `.exe` installers (no Python needed) are planned — for now the
> double-click launchers need Python installed once.

## ⭐ Quick start (guided — no flags to remember)

If you just want a clean inbox and don't care how it works:

```bash
pip install -r requirements.txt

python3 gmail_cleanup.py wizard                    # Gmail
python3 gmail_cleanup.py wizard --provider yahoo   # Yahoo
```

The wizard walks you through everything, in plain language:
1. If it's your first run, it prints the exact steps to create an **app password** and asks
   you to paste it once (hidden). It's stored securely (macOS Keychain, or a locked file).
2. It scans your mailbox and shows your noisiest bulk senders.
3. It asks — in y/N prompts — whether to move that old mail to **Trash** (recoverable) and
   whether to **unsubscribe**. Nothing happens without your yes, and it always previews counts
   before moving anything.

That's the whole journey. Everything below is for people who want the individual commands.

---

## 1. Prerequisites

- Python 3.9+
- `pip install -r requirements.txt` (only `requests`, and only for `unsub-run`)
- A **Gmail or Yahoo** account with **2-Step Verification ON** (required for app passwords)

> **Yahoo users:** the flow is identical — create the app password at
> [login.yahoo.com/account/security](https://login.yahoo.com/account/security) → *Create app
> password* under "External connections", confirm IMAP is on (Yahoo Mail → Settings → More
> Settings → Mailboxes), then use `--provider yahoo` on any command. The `setup`/`wizard`
> commands print these steps for you.

## 2. Create a Gmail app password (step by step)

You never give this tool your real Google password. You create a scoped **app password**.
(Or skip this section entirely and let `python3 gmail_cleanup.py setup` walk you through it.)

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
| `wizard` | **Start here.** Guided end-to-end: setup → scan → confirm → clean → unsubscribe |
| `setup` | Store credentials for a provider (prints the app-password steps) |
| `counts` | Landscape of your mailbox (sizes by category / bulk) |
| `profile --top N` | Tally the noisiest bulk senders |
| `unsub-list --top N` | Senders + unsubscribe method (`1click`/`mailto`/`weblink`/`none`) |
| `sweep [--senders a.com,b.com] [--days 365] [--yes]` | Move a sender's old mail to Trash. **Dry-run unless `--yes`.** |
| `unsub-run --domains a.com,b.com` | Execute unsubscribe (one-click POST or mailto/SMTP) |

Add `--provider gmail` (default) or `--provider yahoo` to any command. `sweep` targets by
**sender** (the safe way — see [`RULESET.md`](RULESET.md)); omit `--senders` to target every
non-protected bulk sender. Protected senders (financial/security/gov/transactional) are always
skipped.

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
