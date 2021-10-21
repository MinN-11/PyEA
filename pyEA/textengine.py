
from FE8.definitions import SerifGlyphTable, MenuGlyphTable
import pyEA
import math
from typing import *

NO_NARROW = 0
NARROW = 1
AUTOMATIC = 2

MENU_GLYPHS = []
SERIF_GLYPHS = []

NARROW_MAPPING: Dict[str, str] = {}

NL = "\x01"

text_builder = []


def asciify(string: str):
    string = string.replace('\u2018', "'")
    string = string.replace('\u2019', "'")
    string = string.replace('\u201c', '"')
    string = string.replace('\u201d', '"')
    return string


def populate():
    with pyEA.offset(MenuGlyphTable):
        pyEA.table("menu_glyphs", pyEA.PTR, 256)
    with pyEA.offset(SerifGlyphTable):
        pyEA.table("serif_glyphs", pyEA.PTR, 256)
    for i in range(255):
        for table, name in (MENU_GLYPHS, "menu_glyphs"), (SERIF_GLYPHS, "serif_glyphs"):
            with pyEA.row(name, i):
                ptr = pyEA.peek(pyEA.PTR)
                if ptr == 0:
                    table.append(0)
                else:
                    with pyEA.offset(ptr):
                        pyEA.advance(5)
                        table.append(pyEA.peek(pyEA.BYTE))


def to_narrow(string: str):
    return "".join([NARROW_MAPPING.get(x, x) for x in string])


def measure_string(string: str, menu=False):
    length = 0
    table = MENU_GLYPHS if menu else SERIF_GLYPHS
    for i in string:
        length += table[ord(i)]
    return length


def __draw(menu, space, string, width):
    current = ""
    buffer = ""
    for word in string.split():
        v = current + (space if len(current) > 0 else "") + word
        l = measure_string(v, menu)
        if l > width:
            buffer += current + NL
            current = word
        else:
            current = v
    buffer += current
    return buffer


def write_flex(string: str, menu=False, width=160, height=1):
    string = asciify(string)
    narrow_string = to_narrow(string)
    length = measure_string(string, menu)
    narrow_length = measure_string(narrow_string, menu)
    lines = math.ceil(length / width)
    narrow_lines = math.ceil(narrow_length / width)
    space = " "
    if narrow_lines > height:
        print(f"Warning: Text out of bound for:\n{string}")
    if narrow_lines < lines:
        string = narrow_string
        space = to_narrow(" ")
    return __draw(menu, space, string, width)


def write_normal(string: str, menu=False, width=160, height=1):
    string = asciify(string)
    length = measure_string(string, menu)
    lines = math.ceil(length / width)
    space = " "
    if lines > height:
        print(f"Warning: Text out of bound for:\n{string}")
    return __draw(menu, space, string, width)


def write_narrow(string: str, menu=False, width=160, height=1):
    string = asciify(string)
    string = to_narrow(string)
    length = measure_string(string, menu)
    lines = math.ceil(length / width)
    space = " "
    if lines > height:
        print(f"Warning: Text out of bound for:\n{string}")
    return __draw(menu, space, string, width)


def write_text(string: str):
    pyEA.write_short(pyEA.current_row("text"))
    with pyEA.row("text"):
        pyEA.write_ptr(f"_text_entry_{len(text_builder)}")
        text_builder.append(string)


def dump_text():
    for i, v in enumerate(text_builder):
        pyEA.label(f"_text_entry_{i}")
        pyEA.write_string(v)
