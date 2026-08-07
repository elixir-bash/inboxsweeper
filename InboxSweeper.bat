@echo off
REM Double-click this on Windows to open the Mail Declutter app in your browser.
cd /d "%~dp0"
python -m pip install -r requirements.txt >nul 2>&1
python inboxsweeper.py serve
pause
