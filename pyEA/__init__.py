import struct
from typing import *
import inspect
import math
import os
from pyEA.npstream import NpStream, StreamRevert
import pyEA.npstream
from pyEA import text
import pyEA.globals as g
import numpy
from pyEA import ups


BUFFER: numpy.ndarray
SOURCE_NAME: str
LABELS: Dict[str, int] = {}
STREAM: Union[NpStream, None] = None
HOOKS: Dict[str, List[int]] = {}
TABLES: Dict[str, Tuple[int, int, int, int]] = {}
TABLE_USAGE: Dict[str, Set] = {}

DATA_MAX = 0

BYTE = "<B"
SHORT = "<H"
INT = "<I"
WORD = "<I"
LONG = "<Q"
PTR1 = "P1"
PTR = "P"
POINTER = "P"
POIN = "P"


def get_offset():
    """Get the offset of the file stream."""
    return STREAM.tell()


def size(data_type: str):
    """Return the size of a data type in bytes.

    :param data_type: one of BYTE, SHORT, INT, WORD, PTR, defined by pyEA
    """
    if data_type == BYTE:
        return 1
    elif data_type == SHORT:
        return 2
    elif data_type == LONG:
        return 8
    return 4


def load_source(source_file: str):
    """Load the file to be modified.

    :param source_file: file name of the source file/ROM, relative to pwd
    """
    global BUFFER, DATA_MAX, STREAM, SOURCE_NAME
    BUFFER = numpy.fromfile(source_file, dtype=numpy.byte)
    STREAM = NpStream(BUFFER, 0)
    DATA_MAX = BUFFER.shape[0]
    SOURCE_NAME = source_file


def expand_data():
    global BUFFER
    s = BUFFER.shape[0]
    s = 2 ** math.ceil(math.log2(s)) * 2 - s
    BUFFER = numpy.pad(BUFFER, ((0, s),))


def output(target_file: str, use_ups: bool = True):
    """
    Write the changes to a target file.

    :param target_file: file name of the target file, relative to pwd
    :param use_ups: if true, create a ups file
    """
    if len(HOOKS) > 0:
        print("Warning: Identifiers missing:")
        print(f"{[i for i in HOOKS]}")
    with open(target_file, "wb") as file:
        file.write(BUFFER[:DATA_MAX].tobytes())
        if use_ups:
            print("Making UPS patch...")
            ups.make_ups(SOURCE_NAME, target_file, target_file[:target_file.index(".")] + ".ups")
        print("Done!")


def offset(position: Union[int, NpStream]):
    """Change the offset to the target location.

    :returns: an object that can revert the offset if used in a with block.
    """
    global STREAM
    ref = StreamRevert(STREAM)
    if isinstance(position, int):
        STREAM = NpStream(BUFFER, position)
    else:
        STREAM = position
    return ref


def alloc(position: Union[int, NpStream], add1: bool = False):
    """"Allocate" data at the target stream and write it's location to current offset as a pointer

    :returns: an object that can revert the offset if used in a with block.
    """
    global STREAM
    ref = StreamRevert(STREAM)
    if isinstance(position, int):
        position = NpStream(BUFFER, position)
    position.align(4)
    if add1:
        write_ptr1(position.tell())
    else:
        write_ptr(position.tell())
    STREAM = position
    return ref


def write_to(array: numpy.ndarray):
    """Redirect the stream to an empty numpy.array

    :returns: an object that can revert the stream if used in a with block.
    """
    global STREAM
    ref = StreamRevert(STREAM)
    STREAM = NpStream(array, 0)
    return ref


def advance(delta: int):
    """Move the offset of the CURRENT STREAM forward by delta.
    """
    STREAM.seek(STREAM.tell() + delta)


def ptr(pointer: int):
    """Convert a offset to a pointer"""
    if pointer == 0:
        return 0
    return 0x8000000 + pointer


def fetch(name: Union[str, int]):
    """Convert an identifier to it's value.
    if the identifier is not yet in scope,
    setup a hook for the label.
    """
    if isinstance(name, int):
        return name
    if name in LABELS:
        return ptr(LABELS[name])
    elif name in g.GLOBALS:
        return g.GLOBALS[name]
    else:
        if name not in HOOKS:
            HOOKS[name] = []
        HOOKS[name].append(get_offset())
        return 0


def bitfield(items: Union[str, int, Collection[Union[str, int]]], prefix: str = ''):
    if isinstance(items, str) or isinstance(items, int):
        items = [items]
    items = [prefix + i if isinstance(i, str) else i for i in items]
    v = 0
    for i in items:
        v |= fetch(i)
    return v


def __masking(value: int, data_type: str):
    if value < 0:
        return value & ((1 << size(data_type) * 8) - 1)
    return value


def write(obj: Union[str, int, Collection[Union[str, int]], bytes, numpy.ndarray], data_type: str = BYTE):
    """Write data of a given type to the current offset

    :param obj: data, could be an int, a string identifier, a collection of them, bytes, or a numpy byte array
    :param data_type: one of the pre-defined data types.
    """
    if isinstance(obj, bytes) or isinstance(obj, numpy.ndarray):
        STREAM.write(obj)
        return
    last_bit = 0
    if not hasattr(obj, '__iter__'):
        obj = [obj]
    if data_type == PTR1:
        data_type = PTR
        last_bit = 1
    if data_type == PTR:
        data_type = WORD
        obj = [ptr(i) if isinstance(i, int) else i for i in obj]

    for i in obj:
        if isinstance(i, str):
            STREAM.write(struct.pack(data_type, __masking(fetch(i) | last_bit, data_type)))
        else:
            STREAM.write(struct.pack(data_type, __masking(i | last_bit, data_type)))


def write_byte(*obj: Union[str, int]):
    write(obj, BYTE)


def write_short(*obj: Union[str, int]):
    write(obj, SHORT)


def write_word(*obj: Union[str, int]):
    write(obj, WORD)


def write_ptr(*obj: Union[str, int]):
    write(obj, PTR)


def write_ptr1(*obj: Union[str, int]):
    write(obj, PTR1)


def write_string(string: str):
    buffer = numpy.array([ord(i) for i in string] + [0], dtype=numpy.ubyte).tobytes()
    write(buffer)


def memcpy(src, tar, size):
    BUFFER[tar: tar + size] = BUFFER[src: src + size]


def peek_bytes(size):
    return STREAM.peek(size)


def peek(data_type: str) -> int:
    if data_type == PTR:
        value = STREAM.peek(4)
        v = struct.unpack(WORD, value)[0]
        if v == 0:
            return 0
        return v - 0x8000000
    value = STREAM.peek(size(data_type))
    return struct.unpack(data_type, value)[0]


def write_mask(byte: int, mask: int):
    src = peek(BYTE)
    write(mask & byte + src & (0xFF - mask), BYTE)


def align(bytes: int = 4):
    STREAM.align(bytes)


def is_aligned(bytes: int = 4):
    return get_offset() % bytes == 0


def script(func: Callable) -> Callable:
    def wrapper():
        label(func.__name__)
        func()
    return wrapper


def label(name: str, bytes: int = 4) -> int:
    align(bytes)
    data = STREAM.tell()
    if name != "_":
        LABELS[name] = data
        if name in HOOKS:
            for hook in HOOKS[name]:
                with offset(hook):
                    write(data, PTR)
            HOOKS.pop(name)
    return ptr(get_offset())


def text_label(name: str, bytes: int = 4) -> int:
    align(bytes)
    data = STREAM.tell()
    if name != "_":
        LABELS[name] = data
        if name in HOOKS:
            for hook in HOOKS[name]:
                with offset(hook):
                    write(data | 0x80000000, PTR)
            HOOKS.pop(name)
    return ptr(get_offset())


def table_from(pointer_address: int, table_name: str, row_shape: Union[int, str, Collection[str]],
               num_rows: int, free: int = 0):
    with offset(pointer_address):
        with offset(peek(PTR)):
            table(table_name, row_shape, num_rows, free)


def table(table_name: str, row_shape: Union[int, str, Collection[str]],
          num_rows: int, free: int = 0, default_row: bytes = b""):
    label(table_name)
    if isinstance(row_shape, str):
        row_shape = size(row_shape)
    elif not isinstance(row_shape, int):
        row_shape = sum([size(i) for i in row_shape])
    advance(row_shape * num_rows)
    TABLES[table_name] = LABELS[table_name], row_shape, free, num_rows
    if default_row != b"":
        default_row = numpy.frombuffer(default_row, dtype=numpy.ubyte)
        with offset(LABELS[table_name]):
            STREAM.write(numpy.tile(default_row, num_rows))
    TABLE_USAGE[table_name] = set()


def repoint(table_name: str, count: int, pointers: Collection[int], source_offset: int = 0):
    if source_offset == 0:
        with offset(next(i for i in pointers)):
            source_offset = peek(PTR)
    target_offset = LABELS[table_name]
    memcpy(source_offset, target_offset, count * TABLES[table_name][1])
    for i in pointers:
        with offset(i):
            write_ptr(target_offset)


def _row_advance(table_name: table):
    position, row_len, row_num, num_rows = TABLES[table_name]
    while row_num in TABLE_USAGE[table_name]:
        row_num += 1
    TABLES[table_name] = position, row_len, row_num, num_rows


def current_row(table_name: str):
    _row_advance(table_name)
    _, _, row_num, _ = TABLES[table_name]
    return row_num


def row(table_name: str, row_number: int = -1, data_type: str = ""):
    position, row_len, row_num, max_rows = TABLES[table_name]
    if row_number == -1:
        _row_advance(table_name)
        _, _, row_number, _ = TABLES[table_name]
        TABLES[table_name] = position, row_len, row_number + 1, max_rows
    if data_type != "":
        write(row_number, data_type)
    if row_number >= max_rows:
        print(f"Warning: Writing to row {row_number} on table {table_name} at {hex(position)} with {max_rows} rows.")
    TABLE_USAGE[table_name].add(row_number)
    return offset(position + row_len * row_number)


import pyEA.assets as assets


def load(file_name: str):
    full = os.path.dirname(inspect.stack()[1].filename)
    full = os.path.join(full, file_name)

    path, file = os.path.split(full)
    for ext in assets.ASSET_TYPES:
        if file.endswith(ext):
            if assets.ASSET_TYPES[ext] is None:
                with open(full, "rb") as file:
                    buffer = file.read()
                    STREAM.write(buffer)
            else:
                base = file[:-len(ext)]
                buffer = assets.ASSET_TYPES[ext](path, base)
                STREAM.write(buffer)
            return
    print(f"Warning: Unknown file extension in {file}.")


def load_folder(folder):
    full = os.path.dirname(inspect.stack()[1].filename)
    full = os.path.join(full, folder)
    for root, dirs, files in os.walk(full):
        for file in files:
            for ext in assets.ASSET_TYPES:
                if file.endswith(ext):
                    load(os.path.join(root, file))


def expose(file_name, expose_globals=False):
    buffer = ""
    for i in LABELS:
        if not i.startswith("_"):
            buffer += f"#define {i} {hex(LABELS[i])}\n"
    if expose_globals:
        for i in globals.GLOBALS:
            if not i.startswith("_"):
                buffer += f"#define {i} {hex(globals.GLOBALS[i])}\n"
    with open(file_name, "w") as file:
        file.write(buffer)

