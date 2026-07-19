#!/usr/bin/env bash
set -e
echo "Installing Pokkie v0.4…"
python3 -m pip install --upgrade pip
# Install core + automation extras; pygetwindow is auto-skipped on non-Windows via the marker.
python3 -m pip install --upgrade ".[automation]"
echo ""
echo "Done. Run:  pokkie"
