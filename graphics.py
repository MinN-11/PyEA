import numpy
from typing import *
import struct


def to_gba(arr: numpy.ndarray):
    arr = arr.astype('<u1')
    buffer = split8x8(arr).flatten()
    buffer = (buffer[1::2] << 4) + buffer[::2]
    return buffer


def split8x8(arr: numpy.ndarray):
    h, w = arr.shape
    return arr.reshape(h // 8, 8, -1, 8).swapaxes(1, 2).reshape(-1, 8, 8)


def palette_to_bytes(palette: Collection[Tuple[int, int, int]]):
    buffer = b""
    f = lambda x: (x >> 3) & 0x1f
    for r, g, b in palette:
        dr, dg, db = f(r), f(g), f(b)
        v = dr + (dg << 5) + (db << 10)
        buffer += struct.pack("<H", v)
    return buffer