"""Эмулятор оболочки UNIX-подобной ОС. Этап 3: VFS."""

import argparse
import os
import shlex
import sys

from vfs import VfsError, describe, get_current, load_vfs, set_current

DEFAULT_VFS_NAME = "myvfs"
PROMPT_SUFFIX = "$ "
NOT_SET = "(не задан)"
COMMENT_MARK = "#"
EXIT_OK = 0
EXIT_ERROR = 1
MAX_CD_ARGS = 1


class ShellError(Exception):
    """Ошибка выполнения команды оболочки."""


def make_prompt(vfs_name=DEFAULT_VFS_NAME):
    """Возвращает приглашение к вводу с именем VFS."""
    return f"{vfs_name}:{PROMPT_SUFFIX}"


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


def print_stub(name, args):
    """Печатает имя команды-заглушки и её аргументы."""
    print(f"{name}: аргументы = {args}")


def cmd_ls(args):
    """Заглушка команды ls."""
    print_stub("ls", args)


def cmd_cd(args):
    """Заглушка команды cd. Принимает не более одного аргумента."""
    if len(args) > MAX_CD_ARGS:
        raise ShellError("cd: слишком много аргументов")
    print_stub("cd", args)


def cmd_exit(args):
    """Завершает работу эмулятора."""
    if args:
        raise ShellError("exit: команда не принимает аргументов")
    raise SystemExit(EXIT_OK)


def cmd_vfs_info(args):
    """Служебная команда: сводка по загруженной VFS (только чтение)."""
    if args:
        raise ShellError("vfs-info: команда не принимает аргументов")
    current = get_current()
    if current is None:
        raise ShellError("vfs-info: VFS не загружена")
    print(describe(current))


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
    "vfs-info": cmd_vfs_info,
}


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
        print(f"{prompt}{line}")
        try:
            execute_line(line)
        except ShellError as error:
            message = f"ошибка в строке {number} скрипта: {error}"
            print(message, file=sys.stderr)


def repl(prompt):
    """Запускает интерактивный цикл REPL."""
    while True:
        try:
            line = input(prompt)
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
    prompt = make_prompt(vfs_name_from_path(args.vfs))
    if args.script:
        run_script(args.script, prompt)
    repl(prompt)


if __name__ == "__main__":
    main()
