#!/bin/sh
# VFS минимальный: пустой корневой каталог.
cd "$(dirname "$0")/.." || exit 1
echo "=== VFS: минимальный ==="
python3 src/emulator.py --vfs vfs/minimal.json \
    --script scripts/data/info.emu
