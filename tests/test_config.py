"""Тесты этапа 2: параметры запуска и стартовый скрипт."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import emulator

PROMPT = "vfs:$ "


def run_script_text(text):
    """Выполняет скрипт с заданным текстом, возвращает (stdout, stderr)."""
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "start.emu")
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            emulator.run_script(path, PROMPT)
    return out.getvalue(), err.getvalue()


class ArgsTests(unittest.TestCase):
    """Проверки параметров командной строки."""

    def test_no_args(self):
        """Без параметров значения не заданы."""
        args = emulator.parse_args([])
        self.assertIsNone(args.vfs)
        self.assertIsNone(args.script)

    def test_both_args(self):
        """Оба параметра читаются."""
        args = emulator.parse_args(["--vfs", "a.json", "--script", "s.emu"])
        self.assertEqual(args.vfs, "a.json")
        self.assertEqual(args.script, "s.emu")

    def test_vfs_name(self):
        """Имя VFS берётся из имени файла."""
        name = emulator.vfs_name_from_path("dir/disk.json")
        self.assertEqual(name, "disk.json")

    def test_vfs_name_default(self):
        """Без пути используется имя по умолчанию."""
        name = emulator.vfs_name_from_path(None)
        self.assertEqual(name, emulator.DEFAULT_VFS_NAME)

    def test_debug_output(self):
        """Отладочный вывод содержит все параметры."""
        args = emulator.parse_args(["--vfs", "a.json"])
        out = io.StringIO()
        with redirect_stdout(out):
            emulator.print_config(args)
        self.assertIn("a.json", out.getvalue())
        self.assertIn(emulator.NOT_SET, out.getvalue())


class ScriptTests(unittest.TestCase):
    """Проверки стартового скрипта."""

    def test_input_and_output_shown(self):
        """На экране виден и ввод, и вывод."""
        out, _ = run_script_text("ls a\n")
        self.assertIn(PROMPT + "ls a", out)
        self.assertIn("ls: аргументы", out)

    def test_errors_skipped(self):
        """Ошибочные строки пропускаются, остальные выполняются."""
        out, err = run_script_text("foo\nls x\n")
        self.assertIn("строке 1", err)
        self.assertIn("ls: аргументы", out)

    def test_comments_and_blank(self):
        """Комментарии и пустые строки не выполняются."""
        out, _ = run_script_text("# note\n\nls\n")
        self.assertNotIn("note", out)

    def test_missing_script(self):
        """Отсутствующий скрипт вызывает сообщение об ошибке."""
        err = io.StringIO()
        with redirect_stderr(err):
            emulator.run_script("/no/such/file.emu", PROMPT)
        self.assertIn("скрипт не прочитан", err.getvalue())


if __name__ == "__main__":
    unittest.main()
