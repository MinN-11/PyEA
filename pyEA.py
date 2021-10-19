from io import BytesIO
import struct
from typing import *
import globals
import assets
import inspect
import os
import zlib
from offset import TempOffset

STREAM: BinaryIO
BUFFER: bytearray
LABELS: Dict[str, int] = {}
HOOKS: Dict[str, List[int]] = {}
TABLES: Dict[str, Tuple[int, int, int, int]] = {}

BYTE = "<B"
SHORT = "<H"
INT = "<I"
LONG = "<Q"
WORD = "<Q"
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
    elif data_type == INT:
        return 2
    return 4


def load_source(source_file: str):
    """Load the file to be modified.

    :param source_file: file name of the source file/ROM, relative to pwd
    """
    global BUFFER, STREAM
    with open(source_file, "rb") as file:
        BUFFER = bytearray(file.read())
        STREAM = BytesIO(BUFFER)


def output(target_file: str):
    """
    Write the changes to a target file.

    :param target_file: file name of the target file, relative to pwd
    """
    with open(target_file, "wb") as file:
        file.write(BUFFER)


def offset(position: int):
    """Change the offset to the target location.

    :returns: an object that reverts the offset if used in a with block.
    """
    prev = get_offset()
    revert = TempOffset(prev)
    STREAM.seek(position)
    return revert


def advance(delta: int):
    """Move the offset forward by delta.
    :returns: an object that reverts the offset if used in a with block.
    """
    prev = get_offset()
    revert = TempOffset(prev)
    STREAM.seek(prev + delta)
    return revert


def thumb(pointer: int):
    """Convert a pointer to a thumb pointer"""
    return pointer | 1


def ptr(pointer: int):
    """Convert a offset to a pointer"""
    if pointer == 0:
        return 0
    return 0x8000000 + pointer


def fetch(name: str):
    """Convert an identifier to it's value.
    if the identifier is not yet in scope,
    setup a hook for the label.
    """
    if name in LABELS:
        return ptr(LABELS[name])
    elif hasattr(globals, name):
        return getattr(globals, name)
    else:
        if name not in HOOKS:
            HOOKS[name] = []
        HOOKS[name].append(get_offset())
        return 0


def __masking(value: int, data_type: str):
    if value < 0:
        return value & ((1 << size(data_type) * 8) - 1)
    return value


def write(obj: Union[str, int, Collection[Union[str, int]]], data_type: str):
    """Write data of a given type to the current offset

    :param obj: data, could be an int, a string identifier, or a collection of them
    :param data_type: one of the pre-defined data types.
    """

    if not hasattr(obj, '__iter__'):
        obj = [obj]
    if data_type == PTR:
        data_type = WORD
        obj = [ptr(i) if isinstance(i, int) else i for i in obj]

    for i in obj:
        if isinstance(i, str):
            STREAM.write(struct.pack(data_type, __masking(fetch(i), data_type)))
        else:
            STREAM.write(struct.pack(data_type, __masking(i, data_type)))


def write_int(*obj: Union[str, int]):
    write(obj, INT)


def write_short(*obj: Union[str, int]):
    write(obj, SHORT)


def write_byte(*obj: Union[str, int]):
    write(obj, BYTE)


def write_word(*obj: Union[str, int]):
    write(obj, WORD)


def write_ptr(*obj: Union[str, int]):
    write(obj, PTR)


def peek(data_type: str) -> int:
    with label("_", 1):
        value = STREAM.read(size(data_type))
        if data_type == PTR:
            data_type = WORD
        return struct.unpack(data_type, value)[0]


def write_mask(byte: int, mask: int):
    src = peek(BYTE)
    write(mask & byte + src & (0xFF - mask), BYTE)


def align(bytes: int = 4):
    offset((get_offset() + bytes - 1) // bytes * bytes)


def label(name: str, bytes: int = 4) -> int:
    align(bytes)
    if name != "_":
        LABELS[name] = get_offset()
        if name in HOOKS:
            data = get_offset()
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
    elif not isinstance(row, int):
        row_shape = sum([size(i) for i in row_shape])
    advance(row_shape * num_rows)
    TABLES[table_name] = LABELS[table_name], row_shape, free, num_rows
    if default_row != b"":
        for i in range(free, num_rows):
            with row(table_name, i):
                STREAM.write(default_row)


def row(table_name: str, row_number: int = -1):
    position, row_len, row_num, num_rows = TABLES[table_name]
    if row_number == -1:
        row_number = row_num
    if row_number >= num_rows:
        print(f"Warning: Writing to row {row_number} on table {table_name} at {hex(position)} with {num_rows} rows.")
    return offset(position)


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
