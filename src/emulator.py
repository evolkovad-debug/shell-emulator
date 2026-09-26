"""Эмулятор оболочки UNIX-подобной ОС. Этап 4: основные команды."""

import argparse
import os
import shlex
import sys

from commands import COMMANDS
from errors import ShellError
from vfs import (
    VfsError, empty_vfs, get_current, load_vfs, path_to_str, set_current,
)

DEFAULT_VFS_NAME = "myvfs"
PROMPT_SUFFIX = "$ "
NOT_SET = "(не задан)"
COMMENT_MARK = "#"
EXIT_ERROR = 1
ROOT_DIR = "/"


def make_prompt(vfs_name=DEFAULT_VFS_NAME, cwd=ROOT_DIR):
    """Возвращает приглашение к вводу: имя VFS и текущий каталог."""
    return f"{vfs_name}:{cwd}{PROMPT_SUFFIX}"


def current_prompt():
    """Приглашение для загруженной VFS с учётом текущего каталога."""
    current = get_current()
    if current is None:
        return make_prompt()
    return make_prompt(current.name, path_to_str(current.cwd))


def render_prompt(prompt):
    """Приглашение может быть строкой или функцией без аргументов."""
    return prompt() if callable(prompt) else prompt


def vfs_name_from_path(path):
    """Возвращает имя VFS: имя файла из пути или имя по умолчанию."""
    if not path:
        return DEFAULT_VFS_NAME
    return os.path.basename(path) or DEFAULT_VFS_NAME


def parse_line(line):
    """Разбирает строку на команду и аргументы с учётом кавычек.

    Возвращает список токенов. При незакрытой кавычке
    выбрасывает ShellError.
    """
    try:
        return shlex.split(line)
    except ValueError as error:
        raise ShellError(f"ошибка разбора: {error}") from error


def execute(tokens):
    """Выполняет команду, заданную списком токенов."""
    if not tokens:
        return
    name, args = tokens[0], tokens[1:]
    handler = COMMANDS.get(name)
    if handler is None:
        raise ShellError(f"{name}: команда не найдена")
    handler(args)


def execute_line(line):
    """Разбирает и выполняет строку. Ошибки выбрасываются наружу."""
    execute(parse_line(line))


def run_line(line):
    """Выполняет одну строку, выводя ошибки в stderr."""
    try:
        execute_line(line)
    except ShellError as error:
        print(error, file=sys.stderr)


def parse_args(argv=None):
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки UNIX-подобной ОС"
    )
    parser.add_argument(
        "--vfs", metavar="ПУТЬ",
        help="путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--script", metavar="ПУТЬ",
        help="путь к стартовому скрипту",
    )
    return parser.parse_args(argv)


def print_config(args):
    """Выводит отладочную информацию обо всех заданных параметрах."""
    print("[debug] параметры запуска:")
    print(f"[debug]   vfs    = {args.vfs or NOT_SET}")
    print(f"[debug]   script = {args.script or NOT_SET}")


def read_script(path):
    """Читает строки стартового скрипта. При ошибке — ShellError."""
    try:
        with open(path, encoding="utf-8") as file:
            return file.read().splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ShellError(f"скрипт не прочитан: {error}") from error


def is_skipped(line):
    """Пустые строки и строки-комментарии в скрипте пропускаются."""
    stripped = line.strip()
    return not stripped or stripped.startswith(COMMENT_MARK)


def run_script(path, prompt):
    """Выполняет стартовый скрипт, имитируя диалог с пользователем.

    Ошибочные строки пропускаются, об ошибке сообщается в stderr.
    """
    try:
        lines = read_script(path)
    except ShellError as error:
        print(error, file=sys.stderr)
        return
    for number, line in enumerate(lines, start=1):
        if is_skipped(line):
            continue
        print(f"{render_prompt(prompt)}{line}")
        try:
            execute_line(line)
        except ShellError as error:
            message = f"ошибка в строке {number} скрипта: {error}"
            print(message, file=sys.stderr)


def repl(prompt):
    """Запускает интерактивный цикл REPL."""
    while True:
        try:
            line = input(render_prompt(prompt))
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue
        run_line(line)


def load_configured_vfs(path):
    """Загружает VFS из файла. При ошибке сообщает о ней и выходит."""
    try:
        set_current(load_vfs(path))
    except VfsError as error:
        print(f"ошибка загрузки VFS: {error}", file=sys.stderr)
        raise SystemExit(EXIT_ERROR) from error


def main(argv=None):
    """Точка входа: параметры, VFS, скрипт, затем REPL."""
    args = parse_args(argv)
    print_config(args)
    if args.vfs:
        load_configured_vfs(args.vfs)
    else:
        set_current(empty_vfs(DEFAULT_VFS_NAME))
    if args.script:
        run_script(args.script, current_prompt)
    repl(current_prompt)


if __name__ == "__main__":
    main()
