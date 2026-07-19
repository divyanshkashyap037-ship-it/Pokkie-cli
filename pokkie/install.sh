#!/usr/bin/env bash
set -e
echo ""
echo "============================================"
echo "  Installing Pokkie v0.2 - AI Terminal Assistant"
echo "============================================"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Install Python 3.9+ first."
    exit 1
fi

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade --force-reinstall .

echo ""
echo "✅ Installed! Run: pokkie"
echo "If Groq says Access denied, run /doctor inside Pokkie."
