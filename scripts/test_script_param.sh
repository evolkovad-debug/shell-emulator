#!/bin/sh
# Параметр --script: скрипт без ошибок.
cd "$(dirname "$0")/.." || exit 1
echo "=== Параметр --script ==="
python3 src/emulator.py --script scripts/data/good.emu
