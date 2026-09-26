#!/bin/sh
# VFS с несколькими файлами (текст, двоичный файл в base64, папка).
cd "$(dirname "$0")/.." || exit 1
echo "=== VFS: несколько файлов ==="
python3 src/emulator.py --vfs vfs/several.json \
    --script scripts/data/info.emu
