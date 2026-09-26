"""Тесты этапа 1: парсер и команды эмулятора."""

import unittest

import emulator


class ParserTests(unittest.TestCase):
    """Проверки разбора строки."""

    def test_simple_split(self):
        """Обычные аргументы разделяются пробелами."""
        self.assertEqual(emulator.parse_line("ls a b"), ["ls", "a", "b"])

    def test_quoted_argument(self):
        """Аргумент в кавычках остаётся одним целым."""
        tokens = emulator.parse_line('ls "my folder" x')
        self.assertEqual(tokens, ["ls", "my folder", "x"])

    def test_unclosed_quote(self):
        """Незакрытая кавычка приводит к ошибке."""
        with self.assertRaises(emulator.ShellError):
            emulator.parse_line('ls "oops')


class CommandTests(unittest.TestCase):
    """Проверки выполнения команд."""

    def test_unknown_command(self):
        """Неизвестная команда вызывает ошибку."""
        with self.assertRaises(emulator.ShellError):
            emulator.execute(["foo"])

    def test_cd_too_many_args(self):
        """cd с двумя аргументами вызывает ошибку."""
        with self.assertRaises(emulator.ShellError):
            emulator.execute(["cd", "a", "b"])

    def test_exit_with_args(self):
        """exit с аргументами вызывает ошибку."""
        with self.assertRaises(emulator.ShellError):
            emulator.execute(["exit", "now"])

    def test_exit(self):
        """exit завершает программу."""
        with self.assertRaises(SystemExit):
            emulator.execute(["exit"])

    def test_ls_needs_vfs(self):
        """Без загруженной VFS команда ls сообщает об ошибке."""
        with self.assertRaises(emulator.ShellError):
            emulator.execute(["ls"])


if __name__ == "__main__":
    unittest.main()
