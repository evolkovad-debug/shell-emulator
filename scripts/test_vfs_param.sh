#!/bin/sh
# Параметр --vfs: имя VFS попадает в приглашение.
cd "$(dirname "$0")/.." || exit 1
echo "=== Параметр --vfs ==="
printf 'ls\nexit\n' | python3 src/emulator.py --vfs vfs/several.json
