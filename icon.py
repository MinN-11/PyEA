
from PIL import Image
from graphics import to_gba
import numpy
from typing import *
import lz77

GBA_ITEM_PALETTE = (
    (192, 248, 200), (248, 248, 248), (200, 192, 184), (144, 144, 128),
    (40, 56, 32), (216, 208, 32), (160, 8, 8), (56, 80, 240),
    (112, 120, 144), (176, 176, 208), (40, 128, 96), (104, 200, 184),
    (112, 80, 48), (152, 128, 112), (80, 56, 64), (192, 96, 0),
)


def fix_item_icon(image: Image.Image):
    image = image.convert('P', dither=Image.NONE, palette=GBA_ITEM_PALETTE)
    arr = numpy.array(image.getdata(), dtype='<u1').reshape((16, 16))
    buffer = split8x8(arr).flatten()
    buffer = (buffer[1::2] << 4) + buffer[::2]
    return buffer


def load_item_icon(file: str):
    image: Image.Image = Image.open(file)
    palette = image.palette.colors
    for c, v in enumerate(GBA_ITEM_PALETTE):
        if v not in palette or palette[v] != c:
            return fix_item_icon(image)
    arr = numpy.array(image.getdata(), dtype='<u1').reshape((16, 16))
    return to_gba(arr).tobytes()


