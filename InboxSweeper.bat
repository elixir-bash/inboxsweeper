@echo off
title InboxSweeper
cd /d "%~dp0"
cls
echo ===============================================
echo    InboxSweeper - free, private inbox cleanup
echo ===============================================
echo.

REM 1) Find a usable Python launcher
set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)

REM 2) If Python is missing, guide the free, one-time install instead of failing
if not defined PY (
  echo InboxSweeper needs Python 3 - a free, one-time install from python.org.
  echo.
  echo   1. Press a key and I'll open the download page.
  echo   2. IMPORTANT: on the first installer screen, tick
  echo      "Add python.exe to PATH", then click "Install Now".
  echo   3. Come back here and double-click InboxSweeper again.
  echo.
  pause
  start "" "https://www.python.org/downloads/windows/"
  exit /b
)

REM 3) Install the one dependency (quietly) and launch the browser UI
echo Setting up (first run only, ~20s)...
%PY% -m pip install -q -r requirements.txt >nul 2>&1

echo Opening InboxSweeper in your browser...
echo (Keep this window open while you use it - close it when you're done.)
echo.
%PY% inboxsweeper.py serve
pause
