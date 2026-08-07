#!/bin/bash
# Double-click this on macOS to open the Mail Declutter app in your browser.
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt >/dev/null 2>&1
exec python3 inboxsweeper.py serve
