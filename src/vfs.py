"""Виртуальная файловая система (VFS). Хранится только в памяти."""

import base64
import binascii
import json
import os
from dataclasses import dataclass, field

TYPE_DIR = "dir"
TYPE_FILE = "file"
ENCODING_TEXT = "text"
ENCODING_BASE64 = "base64"
TEXT_CODEC = "utf-8"
ROOT_PATH = "/"
SEPARATOR = "/"


class VfsError(Exception):
    """Ошибка загрузки или разбора VFS."""


@dataclass
class File:
    """Файл VFS: содержимое хранится в виде байтов."""

    data: bytes = b""


@dataclass
class Directory:
    """Каталог VFS: вложенные файлы и каталоги по их именам."""

    children: dict = field(default_factory=dict)


@dataclass
class Vfs:
    """Виртуальная файловая система: имя, корень и текущий каталог."""

    name: str
    root: Directory
    cwd: list = field(default_factory=list)


def join_path(parent, name):
    """Склеивает путь каталога и имя узла: ('/a', 'b') -> '/a/b'."""
    return parent.rstrip(SEPARATOR) + SEPARATOR + name


def check_name(name, path):
    """Проверяет имя узла: не пустое и без символа '/'."""
    if not name or SEPARATOR in name:
        raise VfsError(f"{path}: недопустимое имя {name!r}")


def decode_content(node, path):
    """Возвращает содержимое файла в байтах с учётом кодировки."""
    content = node.get("content", "")
    if not isinstance(content, str):
        raise VfsError(f"{path}: content должен быть строкой")
    encoding = node.get("encoding", ENCODING_TEXT)
    if encoding == ENCODING_TEXT:
        return content.encode(TEXT_CODEC)
    if encoding == ENCODING_BASE64:
        try:
            return base64.b64decode(content, validate=True)
        except (binascii.Error, ValueError) as error:
            raise VfsError(f"{path}: неверный base64") from error
    raise VfsError(f"{path}: неизвестная кодировка {encoding!r}")


def build_directory(node, path):
    """Строит каталог из словаря JSON вместе со всем содержимым."""
    children = node.get("children", {})
    if not isinstance(children, dict):
        raise VfsError(f"{path}: children должен быть объектом")
    result = Directory()
    for name, child in children.items():
        check_name(name, path)
        result.children[name] = build_node(child, join_path(path, name))
    return result


def build_node(node, path):
    """Строит узел VFS (файл или каталог) из словаря JSON."""
    if not isinstance(node, dict):
        raise VfsError(f"{path}: узел должен быть объектом")
    kind = node.get("type")
    if kind == TYPE_FILE:
        return File(decode_content(node, path))
    if kind == TYPE_DIR:
        return build_directory(node, path)
    raise VfsError(f"{path}: неизвестный тип {kind!r}")


def parse_vfs(text, name):
    """Разбирает текст JSON и строит VFS в памяти. Ошибки — VfsError."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise VfsError(f"неверный формат JSON: {error}") from error
    root = build_node(data, ROOT_PATH)
    if not isinstance(root, Directory):
        raise VfsError("корень VFS должен быть каталогом")
    return Vfs(name, root)


def load_vfs(path):
    """Читает JSON-файл и загружает VFS в память."""
    try:
        with open(path, encoding=TEXT_CODEC) as file:
            text = file.read()
    except OSError as error:
        raise VfsError(f"файл не прочитан: {error}") from error
    except UnicodeDecodeError as error:
        raise VfsError(f"неверная кодировка файла: {error}") from error
    return parse_vfs(text, os.path.basename(path))


def count_nodes(directory):
    """Считает каталоги, файлы и байты внутри каталога (рекурсивно)."""
    dirs = files = size = 0
    for child in directory.children.values():
        if isinstance(child, Directory):
            sub_dirs, sub_files, sub_size = count_nodes(child)
            dirs += 1 + sub_dirs
            files += sub_files
            size += sub_size
        else:
            files += 1
            size += len(child.data)
    return dirs, files, size


def tree_depth(directory):
    """Возвращает число уровней вложенности (файлы тоже уровень)."""
    deepest = 0
    for child in directory.children.values():
        if isinstance(child, Directory):
            deepest = max(deepest, tree_depth(child))
    return deepest + 1 if directory.children else 0


def describe(vfs):
    """Возвращает строку со сводкой по VFS."""
    dirs, files, size = count_nodes(vfs.root)
    depth = tree_depth(vfs.root)
    return (f"VFS {vfs.name}: каталогов {dirs}, файлов {files}, "
            f"байт {size}, уровней {depth}")


_STATE = {"current": None}


def set_current(vfs):
    """Запоминает загруженную VFS (или None) для команд оболочки."""
    _STATE["current"] = vfs


def get_current():
    """Возвращает загруженную VFS или None, если её нет."""
    return _STATE["current"]


CURRENT_DIR = "."
PARENT_DIR = ".."
EMPTY_NAME = ""


class PathError(Exception):
    """Ошибка поиска пути в VFS (нет такого узла, не каталог)."""


def empty_vfs(name):
    """Создаёт пустую VFS: один пустой корневой каталог."""
    return Vfs(name, Directory())


def node_at(root, parts):
    """Возвращает узел по списку имён от корня (пути заведомо верны)."""
    node = root
    for name in parts:
        node = node.children[name]
    return node


def descend(node, name):
    """Возвращает вложенный узел по имени. Ошибки — PathError."""
    if not isinstance(node, Directory):
        raise PathError("не каталог")
    child = node.children.get(name)
    if child is None:
        raise PathError("нет такого файла или каталога")
    return child


def lookup(vfs, text):
    """Находит узел по абсолютному или относительному пути.

    Возвращает пару: (список имён от корня, узел). Ошибки — PathError.
    """
    parts = [] if text.startswith(SEPARATOR) else list(vfs.cwd)
    for name in text.split(SEPARATOR):
        if name in (EMPTY_NAME, CURRENT_DIR):
            continue
        if name == PARENT_DIR:
            del parts[-1:]
        else:
            descend(node_at(vfs.root, parts), name)
            parts.append(name)
    return parts, node_at(vfs.root, parts)


def path_to_str(parts):
    """Превращает список имён в путь: ['a', 'b'] -> '/a/b'."""
    return SEPARATOR + SEPARATOR.join(parts)


def split_path(vfs, text):
    """Делит путь на (родительский каталог, имя узла). Ошибки — PathError."""
    parts, node = lookup(vfs, text)
    if not parts:
        raise PathError("нельзя применить к корню")
    parent = node_at(vfs.root, parts[:-1])
    return parent, parts[-1]


def remove(vfs, text, recursive):
    """Удаляет узел по пути из памяти. Ошибки — PathError."""
    parent, name = split_path(vfs, text)
    node = parent.children[name]
    if isinstance(node, Directory) and node.children and not recursive:
        raise PathError("каталог не пуст (нужен -r)")
    del parent.children[name]
