# Security Policy

InboxSweeper holds your email credentials and deletes mail. That makes security
a product feature, not a formality — please report anything that looks wrong.

## Reporting a vulnerability

**Use GitHub's private reporting:**
[Report a vulnerability](https://github.com/elixir-bash/inboxsweeper/security/advisories/new).
It's private until a fix ships. Please don't open a public issue for anything
that could put someone's mailbox at risk.

Expect a first reply within about a week. This is a free side project, not a
funded product, so there's no bounty and no SLA — just an author who cares.

## What's in scope

- Credentials leaving the machine, being logged, or being written in plaintext
  beyond the documented Keychain / `~/.config/mail-declutter/` paths
- Mail deleted that the sender-selection rules say should be protected
- Anything reaching the local web UI (`serve`) from another origin or host
- Tampering with the released Windows `.exe` or the workflow that builds it
- Personal data in the anonymous telemetry (it should be counts, OS, version —
  nothing else)

## Not in scope

- The unsigned-binary warnings (SmartScreen / Gatekeeper). Known and documented
  in the README — code signing certificates cost money this project doesn't have.
- IMAP provider rate limits and quirks (e.g. Yahoo's 10k cap)
- Anything requiring an attacker who already has your app password

## Verifying what you downloaded

Releases carry build provenance, so you can confirm a binary came from this
repo's workflow rather than someone else:

```
gh attestation verify InboxSweeper.exe --repo elixir-bash/inboxsweeper
```

## Supported versions

The latest release only. Fixes go forward, not into old tags.
