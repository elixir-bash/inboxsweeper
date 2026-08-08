#!/bin/bash
# Double-click to run InboxSweeper. It opens in your web browser.
# Everything runs on your own Mac — nothing is uploaded anywhere.
cd "$(dirname "$0")"
clear
echo "==============================================="
echo "   InboxSweeper — free, private inbox cleanup"
echo "==============================================="
echo

# 1) Find a usable Python 3 (>= 3.9)
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && \
     "$c" -c 'import sys; exit(0 if sys.version_info >= (3,9) else 1)' >/dev/null 2>&1; then
    PY="$c"; break
  fi
done

# 2) If Python is missing, guide the (free, one-time) install instead of failing
if [ -z "$PY" ]; then
  echo "InboxSweeper needs Python 3 — a free, one-time install from python.org."
  echo
  echo "  1. Press any key and I'll open the download page."
  echo "  2. Run the installer (just click Continue / Install)."
  echo "  3. Come back here and double-click InboxSweeper again."
  echo
  read -n 1 -s -r -p "Press any key to open the Python download page…"
  open "https://www.python.org/downloads/macos/"
  exit 0
fi

# 3) Install the one dependency (quietly) and launch the browser UI
echo "Setting up (first run only, ~20s)…"
"$PY" -m pip install --user -q -r requirements.txt >/dev/null 2>&1

echo "Opening InboxSweeper in your browser…"
echo "(Keep this window open while you use it — close it when you're done.)"
echo
exec "$PY" inboxsweeper.py serve
