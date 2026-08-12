# Contributing

Thanks for looking. This is a small, deliberately-focused tool maintained by one
person in spare hours — that shapes what's easy to accept.

## What lands easily

- Bug fixes, especially IMAP quirks on providers I can't test against
- Better sender-classification heuristics (fewer false "junk" calls)
- Docs, typos, clearer wording anywhere

## What to ask about first

Open a [discussion](https://github.com/elixir-bash/inboxsweeper/discussions)
before building anything large. Two constraints aren't negotiable, because
they're the whole point of the project:

1. **Nothing leaves the user's machine.** No uploads, no telemetry beyond the
   existing anonymous counts, no phoning home with anything derived from mail.
2. **No OAuth / "Sign in with Google".** App passwords over IMAP, on purpose.

Also: the tool should stay small. Cleaning, unsubscribing, reporting spam. A PR
that adds a category of feature is a conversation, not a surprise.

## Running it

```
pip install -r requirements.txt
python inboxsweeper.py wizard          # interactive
python inboxsweeper.py serve           # local web UI on 127.0.0.1:8765
```

Test against a mailbox you don't care about. Every destructive command defaults
to a dry run — keep it that way in anything you add.

## Two things that will break if you touch them

- `webui.py`'s `serve()` must stay stdout-safe (use `_say`), or the `--windowed`
  PyInstaller build crashes on launch.
- The macOS Keychain service name `gmail_cleanup` is load-bearing. Renaming it
  orphans every existing user's stored credentials.

## Pull requests

Small and single-purpose is best. Say what you tested against — provider, OS,
and whether you ran it on a real mailbox. There's no CI test suite to hide
behind, so that note is the review.
