#!/bin/sh
# Запуск: ./run.sh        - эмулятор
#         ./run.sh test   - тесты
cd "$(dirname "$0")" || exit 1
if [ "$1" = "test" ]; then
    PYTHONPATH=src python3 -m unittest discover -s tests -v
else
    python3 src/emulator.py
fi
