# Building the standalone installers

Bundles Python + the tool into a double-click app (no Python needed by the end user).
The entry point is `app.py`, which launches the local browser UI (`webui.serve()`).

## Prereqs
```bash
pip install pyinstaller requests
```

## macOS → `InboxSweeper.app`
```bash
pyinstaller --noconfirm --windowed --name InboxSweeper \
  --collect-submodules requests --hidden-import webui --hidden-import inboxsweeper \
  app.py
# → dist/InboxSweeper.app   (zip it for distribution: cd dist && zip -r InboxSweeper-macos.zip InboxSweeper.app)
```

## Windows → `InboxSweeper.exe`
Run on a Windows machine (PyInstaller doesn't cross-compile):
```bat
pyinstaller --noconfirm --onefile --name InboxSweeper ^
  --collect-submodules requests --hidden-import webui --hidden-import inboxsweeper ^
  app.py
REM → dist\InboxSweeper.exe
```

## Notes
- `--windowed` apps have no console, so `webui.serve()` guards its prints (`_say`) — don't
  reintroduce bare `print()` in the serve path or the bundle will crash on launch.
- Unsigned builds trigger Gatekeeper (macOS) / SmartScreen (Windows). Users bypass once via
  right-click → Open. **Signing/notarization** (Apple Developer ID $99/yr; Windows cert)
  removes the warning — that's the roadmap item for a truly one-click experience.
- CI: a GitHub Actions workflow can build both on `macos-latest` + `windows-latest` and attach
  them to a Release on each tag. Adding the workflow file needs a token with `workflow` scope.
