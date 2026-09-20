#!/bin/sh
# Оба параметра вместе.
cd "$(dirname "$0")/.." || exit 1
echo "=== Параметры --vfs и --script ==="
python3 src/emulator.py --vfs vfs/demo.json \
    --script scripts/data/good.emu
