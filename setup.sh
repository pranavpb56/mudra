#!/usr/bin/env bash
# One-shot setup for macOS (Apple Silicon). Usage: ./setup.sh
set -e
PY=""
for p in python3.12 python3.11; do command -v $p >/dev/null 2>&1 && PY=$p && break; done
if [ -z "$PY" ]; then
  echo "Python 3.11/3.12 not found. Installing python@3.12 with Homebrew..."
  command -v brew >/dev/null 2>&1 || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
  brew install python@3.12
  PY=python3.12
fi
$PY -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
mudra init
cat <<MSG

Setup done. Before the first run, give your terminal app these permissions
(System Settings > Privacy & Security):
  - Camera          (to see your hand)
  - Microphone      (for voice commands)
  - Accessibility   (so Mudra can move the cursor and press keys)

Also enable desktop switching shortcuts:
  System Settings > Keyboard > Keyboard Shortcuts > Mission Control
  > "Move left/right a space" (Ctrl+Left / Ctrl+Right)

Run:  source .venv/bin/activate && mudra
MSG
