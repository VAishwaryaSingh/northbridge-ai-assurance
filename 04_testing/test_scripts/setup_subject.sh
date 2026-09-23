#!/usr/bin/env bash
# Clone the system under review at the pinned commit into 04_testing/_subject (read-only use).
# The original Northbridge working tree is never modified.
set -euo pipefail
PIN=9c4127ad65aa5a9e7d362c2d05f69ecfdbf7c5f9
SRC="${NORTHBRIDGE_SRC:-https://github.com/VAishwaryaSingh/Northbridge-Ledger-Agent.git}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/_subject"
rm -rf "$DEST"
git clone --quiet "$SRC" "$DEST"
git -C "$DEST" checkout --quiet "$PIN"
echo "Subject at: $(git -C "$DEST" rev-parse HEAD)"
