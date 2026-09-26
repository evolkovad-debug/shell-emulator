"""Команды оболочки: ls, cd, find, cal, whoami, vfs-info, exit."""

import calendar
import datetime
import fnmatch
import getpass

from errors import ShellError
from vfs import Directory, PathError, describe, get_current, lookup, remove

EXIT_OK = 0
ROOT = "/"
CURRENT = "."
SEP = "/"
SIZE_WIDTH = 6
SINGLE = 1
MAX_CD_ARGS = 1
MAX_CAL_ARGS = 2
YEAR_ONLY = 1
MIN_MONTH, MAX_MONTH = 1, 12
MIN_YEAR, MAX_YEAR = 1, 9999
LS_OPTIONS = {"-l"}
RM_OPTIONS = {"-r"}
MIN_RM_ARGS = 1
FIND_PREDICATES = {"-name", "-type"}
FIND_TYPES = {"f", "d"}


def require_vfs(command):
    """Возвращает загруженную VFS или сообщает об ошибке."""
    current = get_current()
    if current is None:
        raise ShellError(f"{command}: VFS не загружена")
    return current


def find_node(vfs, command, text):
    """Ищет узел по пути; ошибку поиска превращает в ShellError."""
    try:
        return lookup(vfs, text)[1]
    except PathError as error:
        raise ShellError(f"{command}: {text}: {error}") from error


def split_options(command, args, allowed):
    """Делит аргументы на опции вида -x и операнды."""
    options, operands = [], []
    for arg in args:
        if arg.startswith("-") and arg != "-":
            if arg not in allowed:
                raise ShellError(f"{command}: неизвестная опция '{arg}'")
            options.append(arg)
        else:
            operands.append(arg)
    return options, operands


def format_entry(name, node, long_format):
    """Форматирует строку ls для файла или каталога."""
    if not long_format:
        return name
    if isinstance(node, Directory):
        kind, size = "d", 0
    else:
        kind, size = "-", len(node.data)
    return f"{kind} {size:>{SIZE_WIDTH}} {name}"


def print_listing(text, node, long_format, header):
    """Печатает содержимое каталога или строку для одного файла."""
    if not isinstance(node, Directory):
        print(format_entry(text, node, long_format))
        return
    if header:
        print(f"{text}:")
    for name in sorted(node.children):
        print(format_entry(name, node.children[name], long_format))


def cmd_ls(args):
    """ls [-l] [путь...]: содержимое каталогов и файлов."""
    current = require_vfs("ls")
    options, operands = split_options("ls", args, LS_OPTIONS)
    targets = [(text, find_node(current, "ls", text))
               for text in operands or [CURRENT]]
    header = len(targets) > SINGLE
    for index, (text, node) in enumerate(targets):
        if index:
            print()
        print_listing(text, node, "-l" in options, header)


def cmd_cd(args):
    """cd [путь]: смена текущего каталога (без пути — корень)."""
    current = require_vfs("cd")
    if len(args) > MAX_CD_ARGS:
        raise ShellError("cd: слишком много аргументов")
    target = args[0] if args else ROOT
    try:
        parts, node = lookup(current, target)
    except PathError as error:
        raise ShellError(f"cd: {target}: {error}") from error
    if not isinstance(node, Directory):
        raise ShellError(f"cd: {target}: не каталог")
    current.cwd = parts


def take_value(rest, option):
    """Извлекает значение опции find из списка аргументов."""
    if not rest:
        raise ShellError(f"find: для '{option}' не указано значение")
    return rest.pop(0)


def parse_find(args):
    """Разбирает аргументы find: (начало, шаблон имени, тип)."""
    rest = list(args)
    start = CURRENT
    if rest and not rest[0].startswith("-"):
        start = rest.pop(0)
    pattern = kind = None
    while rest:
        option = rest.pop(0)
        if option not in FIND_PREDICATES:
            raise ShellError(f"find: неизвестный предикат '{option}'")
        value = take_value(rest, option)
        if option == "-name":
            pattern = value
        elif value in FIND_TYPES:
            kind = value
        else:
            raise ShellError(f"find: неизвестный тип '{value}'")
    return start, pattern, kind


def walk(display, name, node):
    """Обходит узел и всех потомков; порядок — по именам."""
    yield display, name, node
    if isinstance(node, Directory):
        for child_name in sorted(node.children):
            child = node.children[child_name]
            child_display = display.rstrip(SEP) + SEP + child_name
            yield from walk(child_display, child_name, child)


def is_match(name, node, pattern, kind):
    """Проверяет узел по шаблону имени и типу (f — файл, d — каталог)."""
    if pattern is not None and not fnmatch.fnmatchcase(name, pattern):
        return False
    if kind is None:
        return True
    return isinstance(node, Directory) == (kind == "d")


def cmd_find(args):
    """find [путь] [-name шаблон] [-type f|d]: поиск по дереву VFS."""
    current = require_vfs("find")
    start, pattern, kind = parse_find(args)
    node = find_node(current, "find", start)
    name = start.rstrip(SEP).rsplit(SEP, 1)[-1] or start
    for display, item_name, item in walk(start, name, node):
        if is_match(item_name, item, pattern, kind):
            print(display)


def parse_int(command, text, what, low, high):
    """Переводит текст в число из диапазона [low, high]."""
    try:
        value = int(text)
    except ValueError as error:
        raise ShellError(f"{command}: неверный {what}: {text}") from error
    if not low <= value <= high:
        raise ShellError(f"{command}: {what} вне диапазона: {text}")
    return value


def cmd_cal(args):
    """cal [[месяц] год]: календарь месяца или целого года."""
    if len(args) > MAX_CAL_ARGS:
        raise ShellError("cal: слишком много аргументов")
    text_calendar = calendar.TextCalendar(calendar.SUNDAY)
    today = datetime.date.today()
    if not args:
        print(text_calendar.formatmonth(today.year, today.month).rstrip())
    elif len(args) == YEAR_ONLY:
        year = parse_int("cal", args[0], "год", MIN_YEAR, MAX_YEAR)
        print(text_calendar.formatyear(year).rstrip())
    else:
        month = parse_int("cal", args[0], "месяц", MIN_MONTH, MAX_MONTH)
        year = parse_int("cal", args[1], "год", MIN_YEAR, MAX_YEAR)
        print(text_calendar.formatmonth(year, month).rstrip())


def cmd_whoami(args):
    """whoami: имя текущего пользователя."""
    if args:
        raise ShellError("whoami: лишний операнд")
    try:
        print(getpass.getuser())
    except (KeyError, OSError) as error:
        raise ShellError("whoami: не удалось определить имя") from error


def cmd_rm(args):
    """rm [-r] путь...: удаляет узлы из VFS (только в памяти)."""
    current = require_vfs("rm")
    options, operands = split_options("rm", args, RM_OPTIONS)
    if len(operands) < MIN_RM_ARGS:
        raise ShellError("rm: не указан путь")
    for text in operands:
        try:
            remove(current, text, "-r" in options)
        except PathError as error:
            raise ShellError(f"rm: {text}: {error}") from error


def cmd_vfs_info(args):
    """Служебная команда: сводка по загруженной VFS (только чтение)."""
    if args:
        raise ShellError("vfs-info: команда не принимает аргументов")
    print(describe(require_vfs("vfs-info")))


def cmd_exit(args):
    """Завершает работу эмулятора."""
    if args:
        raise ShellError("exit: команда не принимает аргументов")
    raise SystemExit(EXIT_OK)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "find": cmd_find,
    "cal": cmd_cal,
    "whoami": cmd_whoami,
    "rm": cmd_rm,
    "vfs-info": cmd_vfs_info,
    "exit": cmd_exit,
}
