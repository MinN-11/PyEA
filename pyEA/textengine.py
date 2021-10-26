
from FE8.definitions import SerifGlyphTable, MenuGlyphTable
import pyEA
import math
from typing import *
from varname import varname
from PIL import ImageFont
import pyEA.globals
from pyEA import fontbuilder
import numpy

NO_NARROW = 0
NARROW = 1
AUTOMATIC = 2

MENU_GLYPHS = []
SERIF_GLYPHS = []

NARROW_MAPPING: Dict[str, str] = {}

NL = "\x01"

text_builder = []
glyph_set = [i for i in range(0x20, 0x7b)]


def __init_glyph_tables():
    if "MenuGlyphs" not in pyEA.TABLES:
        with pyEA.offset(MenuGlyphTable):
            pyEA.table("MenuGlyphs", pyEA.PTR, 256)
    if "SerifGlyphs" not in pyEA.TABLES:
        with pyEA.offset(SerifGlyphTable):
            pyEA.table("SerifGlyphs", pyEA.PTR, 256)

def asciify(string: str):
    string = string.replace('\u2018', "'")
    string = string.replace('\u2019', "'")
    string = string.replace('\u201c', '"')
    string = string.replace('\u201d', '"')
    return string


def load_font(file):
    __init_glyph_tables()
    font = ImageFont.truetype(file, 16)
    for i in glyph_set:
        with pyEA.row("SerifGlyphs", i):
            with pyEA.offset(pyEA.peek(pyEA.PTR)):
                pyEA.write_word(0)
                pyEA.write_byte(0)
                glyph = fontbuilder.draw(font, chr(i))
                glyph = fontbuilder.narrowify(glyph) * 3
                buffer = fontbuilder.serif_font(glyph)
                font_size = fontbuilder.glyph_size(buffer) + 1 if chr(i) != ' ' else 2
                buffer = buffer.flatten()
                arr = buffer[::4] + (buffer[1::4] << 2) + (buffer[2::4] << 4) + (buffer[3::4] << 6)
                pyEA.write_byte(font_size)
                pyEA.write_short(0)
                pyEA.write(arr)
        with pyEA.row("MenuGlyphs", i):
            with pyEA.offset(pyEA.peek(pyEA.PTR)):
                pyEA.write_word(0)
                pyEA.write_byte(0)
                glyph = fontbuilder.draw(font, chr(i))
                glyph = fontbuilder.narrowify(glyph) * 3
                buffer = fontbuilder.menu_font(glyph)
                font_size = fontbuilder.glyph_size(buffer) if chr(i) != ' ' else 2
                buffer = buffer.flatten()
                arr = buffer[::4] + (buffer[1::4] << 2) + (buffer[2::4] << 4) + (buffer[3::4] << 6)
                pyEA.write_byte(font_size)
                pyEA.write_short(0)
                pyEA.write(arr)


def build_narrowfont():
    for i in glyph_set:
        with pyEA.row("SerifGlyphs", i):
            with pyEA.offset(pyEA.peek(pyEA.PTR)):
                pyEA.advance(8)
                arr = numpy.frombuffer(pyEA.peek_bytes(64), dtype="<u1")
                base = numpy.zeros(16 * 16, dtype="<u1")
                base[::4] = arr & 0x3
                base[1::4] = (arr >> 2) & 0x3
                base[2::4] = (arr >> 4) & 0x3
                base[3::4] = (arr >> 6) & 0x3

                buffer = base.reshape((16, 16)).astype("<u1")
                buffer = fontbuilder.serif_font(fontbuilder.narrowify(buffer == 3) * 3)
                font_size = fontbuilder.glyph_size(buffer) + 1 if chr(i) != ' ' else 2
                buffer = buffer.flatten()
                arr = buffer[::4] + (buffer[1::4] << 2) + (buffer[2::4] << 4) + (buffer[3::4] << 6)

                with pyEA.row("SerifGlyphs", i):
                    with pyEA.offset(pyEA.peek(pyEA.PTR)):
                        pyEA.advance(5)
                        pyEA.write_byte(font_size)
                        pyEA.advance(2)
                        pyEA.write(arr)

        with pyEA.row("MenuGlyphs", i):
            with pyEA.offset(pyEA.peek(pyEA.PTR)):
                pyEA.advance(8)
                arr = numpy.frombuffer(pyEA.peek_bytes(64), dtype="<u1")
                base = numpy.zeros(16 * 16, dtype="<u1")
                base[::4] = arr & 0x3
                base[1::4] = (arr >> 2) & 0x3
                base[2::4] = (arr >> 4) & 0x3
                base[3::4] = (arr >> 6) & 0x3

                buffer = base.reshape((16, 16)).astype("<u1")
                buffer = fontbuilder.menu_font(fontbuilder.narrowify((buffer == 1) | (buffer == 2)) * 3)
                font_size = fontbuilder.glyph_size(buffer) if chr(i) != ' ' else 2
                buffer = buffer.flatten()
                arr = buffer[::4] + (buffer[1::4] << 2) + (buffer[2::4] << 4) + (buffer[3::4] << 6)

                with pyEA.row("MenuGlyphs", i):
                    with pyEA.offset(pyEA.peek(pyEA.PTR)):
                        pyEA.advance(5)
                        pyEA.write_byte(font_size)
                        pyEA.advance(2)
                        pyEA.write(arr)


def populate():
    __init_glyph_tables()
    for i in range(255):
        for table, name in (MENU_GLYPHS, "MenuGlyphs"), (SERIF_GLYPHS, "SerifGlyphs"):
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


def flex(string: str, menu=False, width=160, height=1):
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


def normal(string: str, menu=False, width=160, height=1):
    string = asciify(string)
    length = measure_string(string, menu)
    lines = math.ceil(length / width)
    space = " "
    if lines > height:
        print(f"Warning: Text out of bound for:\n{string}")
    return __draw(menu, space, string, width)


def narrow(string: str, menu=False, width=160, height=1):
    string = asciify(string)
    string = to_narrow(string)
    length = measure_string(string, menu)
    lines = math.ceil(length / width)
    space = " "
    if lines > height:
        print(f"Warning: Text out of bound for:\n{string}")
    return __draw(menu, space, string, width)


def write_text(string: str, row=-1):
    pyEA.write_short(row if row != -1 else pyEA.current_row("TextTable"))
    with pyEA.row("TextTable", row):
        pyEA.write_ptr(f"_text_entry_{len(text_builder)}")
        text_builder.append(string)


def write_flex(string: str, menu=False, width=160, height=1, row=-1):
    write_text(flex(string, menu, width, height), row)


def write_normal(string: str, menu=False, width=160, height=1, row=-1):
    write_text(normal(string, menu, width, height), row)


def write_narrow(string: str, menu=False, width=160, height=1, row=-1):
    write_text(narrow(string, menu, width, height), row)


def dump_text():
    for i, v in enumerate(text_builder):
        pyEA.text_label(f"_text_entry_{i}")
        pyEA.write_string(v)


# the "comply with event assembler" feature, will be deprecated in the final release
def text_entry(string: str, row: int = -1):
    entry = varname()
    pyEA.globals.set(entry, row if row != -1 else pyEA.current_row("TextTable"))
    with pyEA.row("TextTable", row):
        pyEA.write_ptr(f"_text_entry_{len(text_builder)}")
        text_builder.append(string)
