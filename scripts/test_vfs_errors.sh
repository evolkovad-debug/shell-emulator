#!/bin/sh
# Ошибки загрузки VFS: нет файла, битый JSON, структура, base64.
cd "$(dirname "$0")/.." || exit 1
for name in missing.json bad_json.json bad_structure.json bad_base64.json
do
    echo "=== VFS: $name ==="
    python3 src/emulator.py --vfs "vfs/$name" < /dev/null
    echo "код выхода: $?"
done
