# Building the Windows installer

Most users don't need a build at all:

- **macOS / Linux** — no build. Ship the source; users double-click `InboxSweeper.command`
  (or run `python3 inboxsweeper.py serve`). The launcher installs the one dependency and
  opens the browser UI.
- **Windows** — the only prebuilt binary. A one-file `InboxSweeper.exe` for people who don't
  want to install Python. Built below.

The entry point is `app.py`, which launches the local browser UI (`webui.serve()`).

## Prereqs
```bash
pip install pyinstaller requests
```

## Windows → `InboxSweeper.exe`
Run on a Windows machine (PyInstaller doesn't cross-compile):
```bat
pyinstaller --noconfirm --onefile --name InboxSweeper ^
  --collect-submodules requests --hidden-import webui --hidden-import inboxsweeper ^
  app.py
REM → dist\InboxSweeper.exe
```

In CI this happens automatically: `.github/workflows/release.yml` builds the `.exe` on
`windows-latest` and attaches it to the GitHub Release on each `v*` tag.

## Notes
- `webui.serve()` guards its prints (`_say`) because a windowed/onefile bundle has no console —
  don't reintroduce a bare `print()` in the serve path or the bundle can crash on launch.
- The unsigned `.exe` trips SmartScreen once (**More info → Run anyway**). A signed build
  (Windows code-signing cert) would remove the warning — that's the roadmap item for a truly
  one-click experience.
