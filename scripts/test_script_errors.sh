#!/bin/sh
# Скрипт с ошибочными строками и несуществующий скрипт.
cd "$(dirname "$0")/.." || exit 1
echo "=== Скрипт с ошибками ==="
python3 src/emulator.py --script scripts/data/with_errors.emu < /dev/null
echo "=== Несуществующий скрипт ==="
python3 src/emulator.py --script scripts/data/missing.emu < /dev/null
