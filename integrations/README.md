# Driving InboxSweeper from an AI coding agent

InboxSweeper works with any tool-using coding agent. There are only **two** integration formats,
because most agents share the same `AGENTS.md` standard — so there's one file per format, not one
folder per agent.

| Agent | How it's driven | File |
|---|---|---|
| **Claude Code** | Install as a skill | [`claude-code/SKILL.md`](claude-code/SKILL.md) |
| **Codex** | Reads `AGENTS.md` from the repo root | [`../AGENTS.md`](../AGENTS.md) |
| **Jules** (Google) | Reads `AGENTS.md` from the repo root | [`../AGENTS.md`](../AGENTS.md) |
| **Cursor** | Reads `AGENTS.md` / rules | [`../AGENTS.md`](../AGENTS.md) |
| **Gemini CLI** | Reads `AGENTS.md` from the repo root | [`../AGENTS.md`](../AGENTS.md) |
| **Any other tool-using agent** | Point it at `AGENTS.md` | [`../AGENTS.md`](../AGENTS.md) |

## Claude Code (skill)
```bash
mkdir -p ~/.claude/skills/inboxsweeper
cp integrations/claude-code/SKILL.md inboxsweeper.py ~/.claude/skills/inboxsweeper/
```
Then ask: *"declutter my gmail"* / *"unsubscribe from these senders"* / *"report these as spam"*.

## Codex, Jules, Cursor, Gemini CLI, and everyone else (AGENTS.md)
These agents automatically read [`AGENTS.md`](../AGENTS.md) when it's in the working directory.
Just drop `inboxsweeper.py` + `AGENTS.md` into your project (or run the agent from this repo) and
ask it to clean your inbox. `AGENTS.md` documents the commands, the hard safety rules, and the
recommended flow.

> Whichever agent you use, the same safety rules apply: clean by sender, dry-run first, unsubscribe
> only recognized senders, report unrecognized ones as spam, and never touch financial/security/
> government mail.
