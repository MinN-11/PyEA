
from PIL import Image
from pyEA.graphics import to_gba
import numpy
import zlib
import os

GBA_ITEM_PALETTE = (
    (192, 248, 200), (248, 248, 248), (200, 192, 184), (144, 144, 128),
    (40, 56, 32), (216, 208, 32), (160, 8, 8), (56, 80, 240),
    (112, 120, 144), (176, 176, 208), (40, 128, 96), (104, 200, 184),
    (112, 80, 48), (152, 128, 112), (80, 56, 64), (192, 96, 0),
)


def fix_item_icon(image: Image.Image):
    return image.convert('P', dither=Image.NONE, palette=GBA_ITEM_PALETTE)


def load_item_icon(path: str, file: str):
    image_file = f"{path}/{file}.png"
    asset_file = f"{path}/{file}.asset"
    with open(image_file, "rb") as file:
        crc_image = zlib.crc32(file.read())
    if os.path.isfile(asset_file):
        with open(asset_file, "rb") as file:
            crc = int.from_bytes(file.read(4), "little")
            if crc == crc_image:
                return file.read()
    image: Image.Image = Image.open(image_file)
    palette = image.palette.colors
    for c, v in enumerate(GBA_ITEM_PALETTE):
        if v not in palette or palette[v] != c:
            image = fix_item_icon(image)
            break
    arr = numpy.array(image.getdata(), dtype='<u1').reshape((16, 16))
    buffer = to_gba(arr).tobytes()
    with open(asset_file, "wb") as file:
        file.write(crc_image.to_bytes(4, "little"))
        file.write(buffer)
    return buffer


