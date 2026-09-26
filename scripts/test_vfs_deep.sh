#!/bin/sh
# VFS с вложенностью не менее 3 уровней файлов и папок.
cd "$(dirname "$0")/.." || exit 1
echo "=== VFS: глубокая вложенность ==="
python3 src/emulator.py --vfs vfs/deep.json \
    --script scripts/data/info.emu
