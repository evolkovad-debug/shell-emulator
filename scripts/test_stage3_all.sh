#!/bin/sh
# Стартовый скрипт со всеми командами этапов 1-3 и глубокой VFS.
cd "$(dirname "$0")/.." || exit 1
echo "=== Все команды этапов 1-3 ==="
python3 src/emulator.py --vfs vfs/deep.json \
    --script scripts/data/stage3_all.emu
