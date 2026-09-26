"""Тесты этапа 4: ls, cd, find, cal, whoami и приглашение."""

import calendar
import datetime
import getpass
import io
import json
import unittest
from contextlib import redirect_stdout

import emulator
import vfs

TREE = {
    "type": "dir",
    "children": {
        "a.txt": {"type": "file", "content": "hello"},
        "bin.dat": {"type": "file", "encoding": "base64", "content": "AAEC"},
        "docs": {"type": "dir", "children": {
            "guide.txt": {"type": "file", "content": "Guide"},
            "notes": {"type": "dir", "children": {
                "todo.txt": {"type": "file", "content": "x"},
            }},
        }},
    },
}


def run(*tokens):
    """Выполняет команду и возвращает её вывод построчно."""
    out = io.StringIO()
    with redirect_stdout(out):
        emulator.execute(list(tokens))
    return out.getvalue().splitlines()


class BaseTest(unittest.TestCase):
    """Загружает тестовую VFS перед каждым тестом."""

    def setUp(self):
        """Готовит VFS в памяти."""
        vfs.set_current(vfs.parse_vfs(json.dumps(TREE), "t.json"))

    def tearDown(self):
        """Сбрасывает текущую VFS."""
        vfs.set_current(None)

    def fails(self, *tokens):
        """Проверяет, что команда завершается ошибкой ShellError."""
        with self.assertRaises(emulator.ShellError):
            run(*tokens)


class LsTests(BaseTest):
    """Проверки команды ls."""

    def test_root(self):
        """ls без аргументов показывает корень по алфавиту."""
        self.assertEqual(run("ls"), ["a.txt", "bin.dat", "docs"])

    def test_long_format(self):
        """ls -l показывает тип и размер."""
        lines = run("ls", "-l")
        self.assertTrue(lines[0].startswith("-"))
        self.assertTrue(lines[0].endswith("5 a.txt"))
        self.assertTrue(lines[2].startswith("d"))

    def test_path_and_file(self):
        """ls с путём к каталогу и к файлу."""
        self.assertEqual(run("ls", "docs"), ["guide.txt", "notes"])
        self.assertEqual(run("ls", "a.txt"), ["a.txt"])

    def test_many_paths(self):
        """Несколько путей выводятся с заголовками."""
        lines = run("ls", "docs", "docs/notes")
        expected = ["docs:", "guide.txt", "notes", "",
                    "docs/notes:", "todo.txt"]
        self.assertEqual(lines, expected)

    def test_errors(self):
        """Ошибки: нет пути, неизвестная опция, путь через файл."""
        self.fails("ls", "nosuch")
        self.fails("ls", "-x")
        self.fails("ls", "a.txt/x")


class CdTests(BaseTest):
    """Проверки команды cd и приглашения."""

    def test_relative_and_parent(self):
        """cd вглубь и обратно через '..'."""
        run("cd", "docs/notes")
        self.assertEqual(vfs.get_current().cwd, ["docs", "notes"])
        run("cd", "..")
        self.assertEqual(vfs.get_current().cwd, ["docs"])
        self.assertEqual(run("ls"), ["guide.txt", "notes"])

    def test_absolute_and_home(self):
        """cd по абсолютному пути и без аргументов (корень)."""
        run("cd", "/docs/notes")
        self.assertEqual(vfs.get_current().cwd, ["docs", "notes"])
        run("cd")
        self.assertEqual(vfs.get_current().cwd, [])

    def test_parent_of_root(self):
        """Выше корня подняться нельзя, остаёмся в корне."""
        run("cd", "..")
        self.assertEqual(vfs.get_current().cwd, [])

    def test_errors(self):
        """Ошибки: файл, нет каталога, лишние аргументы."""
        self.fails("cd", "a.txt")
        self.fails("cd", "nosuch")
        self.fails("cd", "a", "b")

    def test_prompt(self):
        """Приглашение содержит имя VFS и текущий каталог."""
        self.assertEqual(emulator.make_prompt("t.json", "/docs"),
                         "t.json:/docs$ ")
        run("cd", "docs")
        self.assertEqual(emulator.current_prompt(), "t.json:/docs$ ")


class FindTests(BaseTest):
    """Проверки команды find."""

    def test_default(self):
        """find без аргументов обходит всё дерево от '.'."""
        expected = [".", "./a.txt", "./bin.dat", "./docs",
                    "./docs/guide.txt", "./docs/notes",
                    "./docs/notes/todo.txt"]
        self.assertEqual(run("find"), expected)

    def test_name(self):
        """Поиск по шаблону имени."""
        expected = ["./a.txt", "./docs/guide.txt", "./docs/notes/todo.txt"]
        self.assertEqual(run("find", "-name", "*.txt"), expected)

    def test_type_and_path(self):
        """Поиск по типу от заданного каталога."""
        self.assertEqual(run("find", "docs", "-type", "d"),
                         ["docs", "docs/notes"])
        self.assertEqual(run("find", "/docs", "-name", "todo.txt"),
                         ["/docs/notes/todo.txt"])

    def test_file_start(self):
        """Начало поиска может быть файлом."""
        self.assertEqual(run("find", "a.txt"), ["a.txt"])

    def test_errors(self):
        """Ошибки: нет пути, нет значения, тип, предикат."""
        self.fails("find", "nosuch")
        self.fails("find", "-name")
        self.fails("find", "-type", "x")
        self.fails("find", "-foo", "x")


class CalWhoamiTests(unittest.TestCase):
    """Проверки команд cal и whoami (VFS не нужна)."""

    def test_cal_month(self):
        """cal месяц год: заголовок и дни недели."""
        lines = run("cal", "9", "2026")
        self.assertEqual(lines[0].strip(), "September 2026")
        self.assertEqual(lines[1].strip(), "Su Mo Tu We Th Fr Sa")

    def test_cal_year_and_current(self):
        """cal год и cal без аргументов."""
        self.assertIn("September", "\n".join(run("cal", "2026")))
        today = datetime.date.today()
        first = run("cal")[0]
        self.assertIn(calendar.month_name[today.month], first)

    def test_cal_errors(self):
        """Ошибки cal: месяц, число, лишние аргументы, год."""
        for args in (("13", "2026"), ("x",), ("1", "2", "3"), ("9", "0")):
            with self.assertRaises(emulator.ShellError):
                run("cal", *args)

    def test_whoami(self):
        """whoami печатает имя пользователя."""
        self.assertEqual(run("whoami"), [getpass.getuser()])
        with self.assertRaises(emulator.ShellError):
            run("whoami", "x")

    def test_no_vfs(self):
        """Без VFS ls, cd и find сообщают об ошибке."""
        vfs.set_current(None)
        for name in ("ls", "cd", "find"):
            with self.assertRaises(emulator.ShellError):
                run(name)


if __name__ == "__main__":
    unittest.main()
