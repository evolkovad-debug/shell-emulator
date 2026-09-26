"""Тесты этапа 3: загрузка VFS в память и служебная команда."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import emulator
import vfs

MINIMAL = {"type": "dir", "children": {}}
NESTED = {
    "type": "dir",
    "children": {
        "a": {"type": "dir", "children": {
            "b": {"type": "dir", "children": {
                "c.txt": {"type": "file", "content": "hi"},
            }},
        }},
        "bin": {"type": "file", "encoding": "base64", "content": "AAEC"},
    },
}


def parse(data):
    """Разбирает словарь как JSON-описание VFS."""
    return vfs.parse_vfs(json.dumps(data), "test.json")


class ParseTests(unittest.TestCase):
    """Проверки разбора корректных VFS."""

    def test_minimal(self):
        """Пустой корневой каталог загружается."""
        result = parse(MINIMAL)
        self.assertEqual(result.root.children, {})

    def test_nested_and_content(self):
        """Вложенные папки и содержимое файлов читаются верно."""
        root = parse(NESTED).root
        file = root.children["a"].children["b"].children["c.txt"]
        self.assertEqual(file.data, b"hi")

    def test_base64_decoded(self):
        """Двоичные данные декодируются из base64."""
        root = parse(NESTED).root
        self.assertEqual(root.children["bin"].data, b"\x00\x01\x02")

    def test_counts_and_depth(self):
        """Подсчёт каталогов, файлов, байтов и уровней."""
        result = parse(NESTED)
        self.assertEqual(vfs.count_nodes(result.root), (2, 2, 5))
        self.assertEqual(vfs.tree_depth(result.root), 3)


class ErrorTests(unittest.TestCase):
    """Проверки ошибок загрузки VFS."""

    def check_error(self, text):
        """Проверяет, что разбор текста вызывает VfsError."""
        with self.assertRaises(vfs.VfsError):
            vfs.parse_vfs(text, "bad.json")

    def test_invalid_json(self):
        """Некорректный JSON."""
        self.check_error('{"type": ')

    def test_root_is_file(self):
        """Корень не может быть файлом."""
        self.check_error('{"type": "file", "content": "x"}')

    def test_unknown_type(self):
        """Неизвестный тип узла."""
        self.check_error('{"type": "dir", "children": {"a": {}}}')

    def test_bad_base64(self):
        """Испорченный base64."""
        node = {"type": "file", "encoding": "base64", "content": "!!"}
        self.check_error(json.dumps({"type": "dir", "children": {"x": node}}))

    def test_bad_name(self):
        """Имя с символом '/' недопустимо."""
        node = {"type": "file", "content": ""}
        self.check_error(json.dumps({"type": "dir", "children": {"a/b": node}}))

    def test_missing_file(self):
        """Отсутствующий файл."""
        with self.assertRaises(vfs.VfsError):
            vfs.load_vfs("/no/such/vfs.json")


class CommandTests(unittest.TestCase):
    """Проверки загрузки из файла и команды vfs-info."""

    def tearDown(self):
        """Сбрасывает текущую VFS после каждого теста."""
        vfs.set_current(None)

    def test_info_without_vfs(self):
        """Без VFS команда сообщает об ошибке."""
        with self.assertRaises(emulator.ShellError):
            emulator.execute(["vfs-info"])

    def test_info_with_vfs(self):
        """С VFS команда печатает сводку."""
        vfs.set_current(parse(NESTED))
        out = io.StringIO()
        with redirect_stdout(out):
            emulator.execute(["vfs-info"])
        self.assertIn("файлов 2", out.getvalue())

    def test_main_bad_vfs_exits(self):
        """Ошибка загрузки VFS завершает программу с кодом 1."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "bad.json")
            with open(path, "w", encoding="utf-8") as file:
                file.write("не json")
            with redirect_stdout(io.StringIO()):
                with redirect_stderr(io.StringIO()) as err:
                    with self.assertRaises(SystemExit) as caught:
                        emulator.main(["--vfs", path])
        self.assertEqual(caught.exception.code, emulator.EXIT_ERROR)
        self.assertIn("ошибка загрузки VFS", err.getvalue())


if __name__ == "__main__":
    unittest.main()
