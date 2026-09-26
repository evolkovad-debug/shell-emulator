"""Тесты этапа 5: команда rm (удаление только в памяти)."""

import json
import unittest

import emulator
import vfs

TREE = {
    "type": "dir",
    "children": {
        "a.txt": {"type": "file", "content": "hi"},
        "docs": {"type": "dir", "children": {
            "guide.txt": {"type": "file", "content": "Guide"},
            "empty": {"type": "dir", "children": {}},
        }},
    },
}


def run(*tokens):
    """Выполняет команду списком токенов."""
    emulator.execute(list(tokens))


class RmTests(unittest.TestCase):
    """Проверки команды rm."""

    def setUp(self):
        """Готовит тестовую VFS перед каждым тестом."""
        vfs.set_current(vfs.parse_vfs(json.dumps(TREE), "t.json"))

    def tearDown(self):
        """Сбрасывает текущую VFS."""
        vfs.set_current(None)

    def test_removes_file(self):
        """Удаление файла убирает его из родительского каталога."""
        run("rm", "a.txt")
        self.assertNotIn("a.txt", vfs.get_current().root.children)

    def test_removes_empty_dir(self):
        """Пустой каталог удаляется без -r."""
        run("rm", "docs/empty")
        self.assertNotIn("empty", vfs.get_current().root.children["docs"]
                          .children)

    def test_non_empty_needs_recursive(self):
        """Непустой каталог без -r удалить нельзя."""
        with self.assertRaises(emulator.ShellError):
            run("rm", "docs")
        run("rm", "-r", "docs")
        self.assertNotIn("docs", vfs.get_current().root.children)

    def test_multiple_paths(self):
        """rm принимает несколько путей за один вызов."""
        run("rm", "a.txt", "docs/empty")
        root = vfs.get_current().root
        self.assertNotIn("a.txt", root.children)
        self.assertNotIn("empty", root.children["docs"].children)

    def test_errors(self):
        """Ошибки: нет пути, несуществующий путь, удаление корня."""
        with self.assertRaises(emulator.ShellError):
            run("rm")
        with self.assertRaises(emulator.ShellError):
            run("rm", "nosuch")
        with self.assertRaises(emulator.ShellError):
            run("rm", "/")

    def test_needs_vfs(self):
        """Без загруженной VFS команда сообщает об ошибке."""
        vfs.set_current(None)
        with self.assertRaises(emulator.ShellError):
            run("rm", "a.txt")

    def test_disk_untouched(self):
        """Удаление никак не связано с диском: файл только в памяти."""
        before = json.dumps(TREE)
        run("rm", "a.txt")
        self.assertEqual(json.dumps(TREE), before)


if __name__ == "__main__":
    unittest.main()
