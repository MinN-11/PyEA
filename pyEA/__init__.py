from io import BytesIO
import struct
from typing import *
import inspect
import math
import os
import zlib
from pyEA.npstream import NpStream, StreamRevert
import pyEA.npstream
import pyEA.assets as assets
import numpy
from varname import varname

BUFFER: numpy.ndarray
LABELS: Dict[str, int] = {}
STREAM: Union[NpStream, None] = None
GLOBALS: Dict[str, int] = {}
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


def define(value: int):
    v = varname()
    GLOBALS[v] = value
    return value


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
    elif data_type == INT:
        return 2
    return 4


def load_source(source_file: str):
    """Load the file to be modified.

    :param source_file: file name of the source file/ROM, relative to pwd
    """
    global BUFFER, DATA_MAX
    BUFFER = numpy.fromfile(source_file, dtype=numpy.byte)
    npstream.STREAM = NpStream(BUFFER, 0)
    DATA_MAX = BUFFER.shape[0]


def expand_data():
    global BUFFER
    s = BUFFER.shape[0]
    s = 2 ** math.ceil(math.log2(s)) * 2
    BUFFER = numpy.resize(BUFFER, s)


def output(target_file: str):
    """
    Write the changes to a target file.

    :param target_file: file name of the target file, relative to pwd
    """
    with open(target_file, "wb") as file:
        file.write(BUFFER[:DATA_MAX].tobytes())


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


def thumb(pointer: int):
    """Convert a pointer to a thumb pointer"""
    return pointer | 1


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
    elif name in GLOBALS:
        return GLOBALS[name]
    else:
        if name not in HOOKS:
            HOOKS[name] = []
        HOOKS[name].append(get_offset())
        return 0


def bitfield(items: Collection[Union[str, int]]):
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


def write_text(string: str):
    pass


def memcpy(src, tar, size):
    BUFFER[tar: tar + size] = BUFFER[src: src + size]


def peek(data_type: str) -> int:
    value = STREAM.peek(size(data_type))
    return struct.unpack(data_type, value)[0]


def write_mask(byte: int, mask: int):
    src = peek(BYTE)
    write(mask & byte + src & (0xFF - mask), BYTE)


def align(bytes: int = 4):
    STREAM.align(bytes)


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


def repoint(table_name: str, source_offset: int, count: int, pointers: Collection[int]):
    target_offset = LABELS[table_name]
    memcpy(source_offset, target_offset, count * TABLES[table_name][1])
    for i in pointers:
        with offset(i):
            write_ptr(target_offset)


def row(table_name: str, row_number: int = -1):
    position, row_len, row_num, num_rows = TABLES[table_name]
    if row_number == -1:
        row_number = row_num
        row_num += 1
    if row_number >= num_rows:
        print(f"Warning: Writing to row {row_number} on table {table_name} at {hex(position)} with {num_rows} rows.")
    return offset(position + row_len * row_number)


def write_row(data_type: str, table_name: str, row_number: int = -1):
    """write the row number to current offset and set offset to row and """
    position, row_len, row_num, num_rows = TABLES[table_name]
    if row_number == -1:
        row_number = row_num
        row_num += 1
    write(row_number, data_type)
    if row_number >= num_rows:
        print(f"Warning: Writing to row {row_number} on table {table_name} at {hex(position)} with {num_rows} rows.")
    return offset(position + row_len * row_number)


def load(file_name: str):
    file = inspect.stack()[1].filename
    path = os.path.dirname(file)
    base, ext = os.path.splitext(file_name)
    base_path = os.path.join(path, file_name)
    compiled_path = os.path.join(path, base + ".asset")
    with open(base_path, "rb") as file:
        buffer = file.read()
        if ext not in assets.ASSET_TYPES or assets.ASSET_TYPES[ext] is None:
            if ext not in assets.ASSET_TYPES:
                print(f"Warning: Unknown file extension {ext} in {file}.")
            STREAM.write(buffer)
            return
        crc = zlib.crc32(buffer)
        if os.path.isfile(compiled_path):
            with open(compiled_path, "rb") as file2:
                buffer2 = file2.read()
                if int.from_bytes(buffer2[:4], byteorder="little") == crc:
                    STREAM.write(buffer2[4:])
                    return
        buffer2 = assets.ASSET_TYPES[ext](buffer)
        with open(compiled_path, "wb") as file2:
            file2.write(crc.to_bytes(4, "little"))
            file2.write(buffer2)
        STREAM.write(buffer2)
