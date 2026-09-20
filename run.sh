#!/bin/sh
# Запуск: ./run.sh [--vfs ПУТЬ] [--script ПУТЬ]  - эмулятор
#         ./run.sh test                          - тесты
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [ "$1" = "test" ]; then
    PYTHONPATH="$ROOT/src" python3 -m unittest discover -s "$ROOT/tests" -v
else
    python3 "$ROOT/src/emulator.py" "$@"
fi
