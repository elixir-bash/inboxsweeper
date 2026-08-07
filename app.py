#!/usr/bin/env python3
"""Bundled desktop-app entry point.

Double-clicking the packaged InboxSweeper app runs this: it starts the local server
and opens the browser UI. Same experience as `inboxsweeper.py serve`, but with Python
and dependencies bundled inside — nothing to install.
"""
import webui

if __name__ == "__main__":
    webui.serve()
