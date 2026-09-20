#!/bin/sh
# Запуск без параметров: ввод берётся из stdin.
cd "$(dirname "$0")/.." || exit 1
echo "=== Без параметров ==="
printf 'ls\nexit\n' | python3 src/emulator.py
