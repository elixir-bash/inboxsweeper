# InboxSweeper

**Clean years of junk out of your inbox — for free, without handing your email to anyone.**

InboxSweeper deletes old promotions and newsletters in bulk and unsubscribes you from the noise.
Built for **Gmail** today, with **experimental** support for **Yahoo and other IMAP** inboxes
(see the note below). It runs entirely on **your own computer**; your email is never uploaded
anywhere. Deleted mail goes to Trash, so you can always get it back.

- 🆓 **Free and open source** — no account, no subscription, no catch.
- 🔒 **Private** — everything happens on your machine; nothing is sent to a company.
- 🧹 **Cleans by who sent it** — clears the junk without touching your receipts, orders, or bookings.
- ✉️ **Actually unsubscribes** — it uses the real one-click unsubscribe, not just delete-and-hope.
- ♻️ **Safe** — deletions go to Trash (recoverable), and bank, security, and government email is protected automatically.
- 🖱️ **Four ways to use it** — a double-click web app, a one-file Windows `.exe`, the terminal, or your AI assistant (Claude / Codex).

**⬇️ Get it:** [Download the app (ZIP)](https://github.com/elixir-bash/inboxsweeper/archive/refs/heads/main.zip) then double-click the launcher inside · or the one-file [Windows .exe](https://github.com/elixir-bash/inboxsweeper/releases/latest/download/InboxSweeper.exe) — or scroll to [the terminal](#the-terminal-for-coders) / [Claude & Codex](#claude-code--codex) options.

> ⚠️ **Read the built-in safety rules before you run a sweep.** The one rule that matters
> most: **recognize a sender → unsubscribe; don't recognize it → report spam, never
> unsubscribe.** Clicking unsubscribe on real spam confirms your address is live and gets
> you *more* spam.

---

## ⚡ Three cleaning modes — you pick the aggression

The heart of InboxSweeper: **one dial from cautious to ruthless.** The wizard asks which mode
you want before it touches anything. Banks, security, payments, receipts and government mail stay
**protected in every mode** — the dial only changes how far back it reaches and how many senders
it clears per run.

| Mode | 🦥 Sloth | 🧹 Normal | 🔥 MadMax |
|---|---|---|---|
| | *safest* | *recommended* | *aggressive* |
| **Reaches** | mail older than **2 years** | mail older than **1 year** | **all** promo mail, incl. recent |
| **Senders / run** | **25** | **50** | **100** |

```bash
python3 inboxsweeper.py wizard              # asks you to pick a mode
python3 inboxsweeper.py sweep --mode madmax # or set it directly on any command
```

Every sweep goes to **Trash** (recoverable ~30 days) and previews the count before anything moves.
Hit the per-run cap? It tells you exactly how many senders remain — just run it again to clear the
next batch.

---

## 🎯 Three actions — and when to use each

The mode above decides *how far back* to reach. Once you've scanned, you choose *what to do* with a
sender. There are three, and picking the right one matters:

| Action | Use it when… | What it does |
|---|---|---|
| ✉️ **Unsubscribe** | you **recognize** the sender | Real one-click / mailto unsubscribe — stops it at the source |
| 🗑️ **Move to Trash** | you're just done with it | Clears the backlog to Trash (recoverable ~30 days) |
| 🚩 **Report spam** | you **don't recognize** it | Trains your provider's filter so future mail auto-junks |

> **The one rule that matters most:** recognize a sender → **unsubscribe**; don't recognize it →
> **report spam, never unsubscribe.** Clicking unsubscribe on real spam confirms your address is
> live and gets you *more* spam. That's why **Report spam** is a **separate, deliberate action** —
> in the app it's its own tab that starts with *nothing* selected, and in the terminal it's the
> `spam` command (or option 2 in the wizard). It never runs in bulk by accident, and it can never
> touch a financial/security/government sender.

---

## Four ways to use it

Pick the one that fits you:

| You are… | Path | In short |
|---|---|---|
| **Anyone** — no tech needed *(recommended)* | **🖱️ Web app** | Download the ZIP, double-click the launcher. Opens in your browser. → [Web app](#-the-web-app-for-everyone) |
| **On Windows, want zero setup** | **📦 One-file .exe** | Download `InboxSweeper.exe`, double-click. → [Windows .exe](#-windows-exe-nothing-else-to-install) |
| **A coder** | **⌨️ Terminal** | `pip install`, then one command. → [Terminal](#the-terminal-for-coders) |
| **A Claude Code / Codex user** | **🤖 Claude skill** | Install the skill and just ask. → [AI agent](#claude-code--codex) |

---

## 🖱️ The web app (for everyone)

Works on **Mac, Windows, and Linux**, always runs the latest version — nothing to compile.

1. **Download the app:** on the [GitHub page](https://github.com/elixir-bash/inboxsweeper), click the
   green **Code** button → **Download ZIP** *(or use this [direct link](https://github.com/elixir-bash/inboxsweeper/archive/refs/heads/main.zip))*.
2. **Unzip it** — double-click on Mac; right-click → *Extract All* on Windows.
3. Open the unzipped folder and **double-click the launcher for your computer:**
   - **🍎 macOS →** `InboxSweeper.command`
     *(first time only: right-click it → **Open** → **Open** to clear the one free-software warning.)*
   - **🪟 Windows →** `InboxSweeper.bat`
   - **🐧 Linux →** `InboxSweeper.command` (or run `python3 inboxsweeper.py serve`)
4. A small window opens and **InboxSweeper appears in your web browser.** Keep that window open while you use it.

It installs its one dependency automatically. **Don't have Python?** The launcher opens the download
page and walks you through the free, one-time install — then just double-click again. From there it's
all clicking: paste an app password once (it shows you exactly how to get one), **Scan**, tick the junk
senders, and hit **Move to Trash** or **Unsubscribe**. Nothing is uploaded; deletions go to Trash.

## 📦 Windows .exe (nothing else to install)

Prefer a true one-file download with **no Python step at all**? On Windows:

1. Download **[InboxSweeper.exe](https://github.com/elixir-bash/inboxsweeper/releases/latest/download/InboxSweeper.exe)**.
2. Double-click it. Windows SmartScreen may warn (free/unsigned) → click **More info → Run anyway**.
3. It opens in your **web browser** — pick Gmail or Yahoo and follow the on-screen steps.

---

## The terminal (for coders)

If you just want a clean inbox and don't care how it works:

```bash
pip install -r requirements.txt

python3 inboxsweeper.py wizard                    # Gmail
python3 inboxsweeper.py wizard --provider yahoo   # Yahoo
```

The wizard walks you through everything, in plain language:
1. First it asks what you want to do: **Clean up** (unsubscribe + move to Trash) or **Report spam**.
2. If it's your first run, it prints the exact steps to create an **app password** and asks
   you to paste it once (hidden). It's stored securely (macOS Keychain, or a locked file).
3. It scans your mailbox and shows your noisiest bulk senders.
4. **Clean up** asks — in y/N prompts — whether to **unsubscribe** (first) then move that mail to
   **Trash**. **Report spam** starts with *nothing* selected and asks which senders to flag.
   Nothing happens without your yes, and it always previews counts before moving anything.

That's the whole journey. Everything below is for people who want the individual commands.

---

## 1. Prerequisites

- Python 3.9+
- `pip install -r requirements.txt` (only `requests`, and only for `unsub-run`)
- A **Gmail or Yahoo** account with **2-Step Verification ON** (required for app passwords)

> **⚠️ Yahoo / other IMAP is experimental.** It works, but with a big caveat: **Yahoo's IMAP only
> exposes your ~10,000 most-recent messages per folder** — older mail simply isn't reachable, and
> Yahoo's server-side search is limited. For a large Yahoo backlog, use **Yahoo's own web
> unsubscribe** (Yahoo Mail → Settings → More Settings → *Subscriptions*), which isn't capped.
> Gmail has no such limits — that's the primary, fully-supported target.
>
> Setup (if you still want it): create an app password at
> [login.yahoo.com/account/security](https://login.yahoo.com/account/security) → *Create app
> password* under "External connections", confirm IMAP is on (Settings → More Settings →
> Mailboxes), then add `--provider yahoo` to any command.

## 2. Create a Gmail app password (step by step)

You never give this tool your real Google password. You create a scoped **app password**.
(Or skip this section entirely and let `python3 inboxsweeper.py setup` walk you through it.)

1. Turn on 2-Step Verification: **[myaccount.google.com/security](https://myaccount.google.com/security)**
   → *2-Step Verification* → follow the steps. (App passwords don't exist without it.)
2. Go to **[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)**.
3. App name: `inboxsweeper` → **Create**.
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
python3 inboxsweeper.py counts

# 2. Rank the noisiest bulk senders (default query = the safe bulk set)
python3 inboxsweeper.py profile --top 40

# 3. Preview a deletion (DRY RUN — nothing moves)
python3 inboxsweeper.py sweep --senders linkedin.com

# 4. Actually move them to Trash (30-day recovery)
python3 inboxsweeper.py sweep --senders linkedin.com --yes

# 5. See each sender's unsubscribe method, then unsubscribe from specific ones
python3 inboxsweeper.py unsub-list --top 40
python3 inboxsweeper.py unsub-run --domains "email-marriott.com,mail.zillow.com,uber.com"
```

### Commands

| Command | Purpose |
|---|---|
| `wizard` | **Start here.** Guided: first pick **Clean up** (unsubscribe + Trash) or **Report spam** |
| `setup` | Store credentials for a provider (prints the app-password steps) |
| `counts` | Landscape of your mailbox (sizes by category / bulk) |
| `profile --top N` | Tally the noisiest bulk senders |
| `unsub-list --top N` | Senders + unsubscribe method (`1click`/`mailto`/`weblink`/`none`) |
| `sweep [--senders a.com,b.com] [--days 365] [--yes]` | Move a sender's old mail to Trash. **Dry-run unless `--yes`.** |
| `unsub-run --domains a.com,b.com` | Execute unsubscribe (one-click POST or mailto/SMTP) |
| `spam --senders a.com,b.com [--yes]` | **Report** specific senders as spam (trains your filter). Deliberate & opt-in — never bulk. **Dry-run unless `--yes`.** |

Add `--provider gmail` (default) or `--provider yahoo` to any command. `sweep` targets by
**sender** (the safe way — see the built-in safety rules); omit `--senders` to target every
non-protected bulk sender. Protected senders (financial/security/gov/transactional) are always
skipped.

## 5. Recommended flow

1. `counts` → find the mass (often it's `category:updates`, which hides receipts).
2. `profile` → rank bulk senders.
3. Classify each into **PROTECT / DELETE / KEEP-BY-DEFAULT** using the built-in safety rules.
4. `sweep` (dry-run → `--yes`) the DELETE set. Verify a sample in Gmail → Bin.
5. `unsub-list` → `unsub-run` the recognized DELETE senders.
6. Unrecognized/spammy senders: **report spam in Gmail — don't unsubscribe.**
7. Add Gmail **filters** for the worst repeat offenders so the backlog can't rebuild.

## The story behind it

I have a habit of pointing a bit of code at the everyday annoyances in my life. For the better part
of 15 years, my inbox was the one that never stayed solved. It started the way these things always
do: a small IMAP script to nuke the obvious promotions. Then another for newsletters. Then a cron
job, once a month, to hold the pile back while I wasn't looking.

The trouble is email never sits still. Every so often something underneath would shift — Google
killed off "less secure app" access and I had to move everything onto 2-factor and app passwords;
the special folders never behaved the same across providers (`[Gmail]/Trash` here, "Bin" there);
IMAP search would quietly change what it returned; Yahoo would only hand back your ten thousand
most-recent messages; a provider would tighten rate limits or rotate a port. The cron would break,
usually silently, and I'd only notice weeks later when the clutter had crept back in. So I patched.
Year after year, one more fix stacked on the last.

But the part I could never fully automate away was the careful bit — the **plumbing and cleaning**.
Bulk-deleting email is easy; bulk-deleting *only* the junk and never once touching what matters is
hard. A bank statement, a flight confirmation, a receipt I'd need at tax time — those can't land in
Trash by accident. So most of my years of tinkering weren't about deleting faster; they were about
drawing the line ever more carefully: expanding the list of protected senders, teaching it to
recognize a financial or government domain, making sure even the most aggressive sweep still
stepped around anything critical.

This year, working with AI, I finally stopped patching the symptoms and fixed the *core*. The
fragile scripts became a real app — the cleaning modes, the safe-by-default sweeps that always go
to Trash, the automatic shield around bank, security and government mail, real one-click
unsubscribe, a browser UI. The whole construct I'd carried in my head for a decade, done properly.
And then the step I'd never gotten around to alone: making it **open source**, so anyone can clean
their inbox the same careful way — for free, and without ever handing their mail to a company.

That's what InboxSweeper is: years of doing this the hard way, finally turned into something anyone
can use.

## How it works

- Connects over IMAP and searches with Gmail's `X-GM-RAW` extension, so any Gmail search
  query works server-side.
- "Delete" = IMAP `MOVE` to the Trash/Bin folder (auto-detected via the `\Trash` special-use
  flag), which is Gmail's 30-day-recoverable trash — not a permanent delete.
- Unsubscribe reads the message's `List-Unsubscribe` / `List-Unsubscribe-Post` headers:
  - **one-click** → HTTP `POST` with body `List-Unsubscribe=One-Click` ([RFC 8058](https://www.rfc-editor.org/rfc/rfc8058)).
  - **mailto** → sends an unsubscribe email via SMTP using your app password.
  - **weblink-only** → reported for manual handling (never auto-clicked; could be a tracker).

## Claude Code / Codex

This repo ships ready-made instructions so an AI coding agent can drive the tool for you.

- **Claude Code** — install as a skill (bundles the script + ruleset so it's self-contained):
  ```bash
  mkdir -p ~/.claude/skills/inboxsweeper
  cp integrations/claude-code/SKILL.md inboxsweeper.py the built-in safety rules ~/.claude/skills/inboxsweeper/
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

## Anonymous usage stats

To show how many people we've helped — and to catch problems — the tool sends **anonymous
counters**: a random install ID, your OS, the tool version, and totals (emails cleaned, MB
freed, unsubscribes). It **never** sends your email address, senders, subjects, or any message
content — your mail still never leaves your machine. Turn it off completely with
`INBOXSWEEPER_NO_TELEMETRY=1`. The live totals appear on the [website](https://elixir-bash.github.io/inboxsweeper/).

## Security

- Uses an **app password**, never your Google password. Revoke it anytime at
  [apppasswords](https://myaccount.google.com/apppasswords) and the tool dies instantly.
- Nothing is hardcoded; credentials come from Keychain or env vars.
- `.gitignore` keeps local credential files out of the repo.

## License

MIT — see [`LICENSE`](LICENSE). Personal tool; use at your own risk. Always dry-run first.

## Author

Built by **Mukundan Govindaraj** — [LinkedIn](https://www.linkedin.com/in/gmukundan/) ·
[GitHub](https://github.com/elixir-bash). If InboxSweeper helps you, a ⭐ on the repo or a
hello on LinkedIn is genuinely appreciated.
