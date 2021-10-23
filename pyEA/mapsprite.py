
from PIL import Image
from pyEA.graphics import to_gba
import numpy
import zlib
import os
import pyEA
from pyEA import lz77

PLAYER_PALETTE = (
    (128, 160, 128), (88, 72, 120), (144, 184, 232), (216, 232, 240),
    (112, 96, 96), (176, 144, 88), (248, 248, 208), (56, 56, 144),
    (56, 80, 224), (40, 160, 248), (24, 240, 248), (232, 16, 24),
    (248, 248, 64), (128, 136, 112), (248, 248, 247), (64, 56, 56),
)


def fix_palette(image: Image.Image):
    return image.convert('P', dither=Image.NONE, palette=PLAYER_PALETTE)


def load_standing_sprite(path: str, file: str, free_space, index: int = -1, pattern=2):
    image_file = f"{path}/{file}.standing.png"
    asset_file = f"{path}/{file}.standing.asset"
    with pyEA.row("StandingMapSprites", index):
        with open(image_file, "rb") as file:
            crc_image = zlib.crc32(file.read())
        if os.path.isfile(asset_file):
            with open(asset_file, "rb") as file:
                crc = int.from_bytes(file.read(4), "little")
                if crc == crc_image:
                    size = file.read(2)
                    buffer = file.read()
                    pyEA.write_short(pattern)
                    pyEA.write(size)
                    with pyEA.alloc(free_space):
                        pyEA.write(buffer)
                    return
        image: Image.Image = Image.open(image_file)
        palette = image.palette.colors
        for c, v in enumerate(PLAYER_PALETTE):
            if v not in palette or palette[v] != c:
                image = fix_palette(image)
                break
        arr = numpy.array(image.getdata(), dtype='<u1')
        if numpy.size(arr) == 16 * 16 * 3:
            arr = arr.reshape((16 * 3, 16))
            size = 0
        elif numpy.size(arr) == 32 * 16 * 3:
            arr = arr.reshape((32 * 3, 16))
            size = 1
        elif numpy.size(arr) == 32 * 32 * 3:
            arr = arr.reshape((32 * 3, 32))
            size = 2
        else:
            raise Exception("Error: Unsupported size of standing map anim.")
        buffer = lz77.compress(to_gba(arr).tobytes())
        pyEA.write_short(pattern)
        pyEA.write(size)
        with pyEA.alloc(free_space):
            pyEA.write(buffer)
        with open(asset_file, "wb") as file:
            file.write(crc_image.to_bytes(4, "little"))
            file.write(size.to_bytes(2, "little"))
            file.write(buffer)


def load_moving_sprite(path: str, file: str, free_space, index: int = -1, ap=0x1C692C):
    image_file = f"{path}/{file}.moving.png"
    asset_file = f"{path}/{file}.moving.asset"
    with pyEA.row("MovingMapSprites", index):
        with open(image_file, "rb") as file:
            crc_image = zlib.crc32(file.read())
        if os.path.isfile(asset_file):
            with open(asset_file, "rb") as file:
                crc = int.from_bytes(file.read(4), "little")
                if crc == crc_image:
                    buffer = file.read()
                    with pyEA.alloc(free_space):
                        pyEA.write(buffer)
                    pyEA.write_ptr(ap)
                    return
        image: Image.Image = Image.open(image_file)
        palette = image.palette.colors
        for c, v in enumerate(PLAYER_PALETTE):
            if v not in palette or palette[v] != c:
                image = fix_palette(image)
                break
        arr = numpy.array(image.getdata(), dtype='<u1').reshape((480, 32))
        buffer = lz77.compress(to_gba(arr).tobytes())
        with pyEA.alloc(free_space):
            pyEA.write(buffer)
        pyEA.write_ptr(ap)
        with open(asset_file, "wb") as file:
            file.write(crc_image.to_bytes(4, "little"))
            file.write(buffer)

