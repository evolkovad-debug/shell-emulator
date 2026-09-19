"""Эмулятор оболочки UNIX-подобной ОС. Этап 1: REPL."""

import shlex
import sys

VFS_NAME = "myvfs"
PROMPT_SUFFIX = "$ "
EXIT_OK = 0
MAX_CD_ARGS = 1


class ShellError(Exception):
    """Ошибка выполнения команды оболочки."""


def make_prompt():
    """Возвращает приглашение к вводу с именем VFS."""
    return f"{VFS_NAME}:{PROMPT_SUFFIX}"


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


COMMANDS = {"ls": cmd_ls, "cd": cmd_cd, "exit": cmd_exit}


def execute(tokens):
    """Выполняет команду, заданную списком токенов."""
    if not tokens:
        return
    name, args = tokens[0], tokens[1:]
    handler = COMMANDS.get(name)
    if handler is None:
        raise ShellError(f"{name}: команда не найдена")
    handler(args)


def run_line(line):
    """Разбирает и выполняет одну строку, выводя ошибки в stderr."""
    try:
        execute(parse_line(line))
    except ShellError as error:
        print(error, file=sys.stderr)


def main():
    """Запускает интерактивный цикл REPL."""
    while True:
        try:
            line = input(make_prompt())
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue
        run_line(line)


if __name__ == "__main__":
    main()
