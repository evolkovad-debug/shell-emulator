#!/bin/sh
# Демонстрация rm: удаление файла, каталога с -r, и ошибки.
cd "$(dirname "$0")/.." || exit 1
echo "=== Команда rm ==="
python3 src/emulator.py --vfs vfs/deep.json \
    --script scripts/data/stage5_rm.emu
