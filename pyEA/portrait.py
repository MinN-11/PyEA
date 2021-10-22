
from PIL import Image
import numpy
from pyEA import lz77
import pyEA
from pyEA.graphics import to_gba, palette_to_bytes
import zlib
import os

HEADER = bytes([0x00, 0x04, 0x10, 0x00])


def cut_image(arr: numpy.array):
    portrait = numpy.zeros((32, 256))
    frames = numpy.zeros((8, 384))

    minimug = arr[16: 48, 96: 128]

    portrait[0: 32, 160: 176] = arr[48: 80, 0: 16]
    portrait[0: 32, 176: 192] = arr[48: 80, 80: 96]
    portrait[0: 32, 0: 64] = arr[0: 32, 16: 80]
    portrait[0: 32, 64: 128] = arr[32: 64, 16: 80]
    portrait[0: 16, 128: 160] = arr[64: 80, 16: 48]
    portrait[16: 32, 128: 160] = arr[64: 80, 48: 80]

    portrait[0: 16, 192: 224] = arr[48: 64, 96: 128]
    portrait[16: 32, 192: 224] = arr[64: 80, 96: 128]
    portrait[0: 16, 224: 256] = arr[80: 96, 96: 128]
    portrait[16: 32, 224: 256] = arr[96: 112, 96: 128]

    frames[:, 0: 32] = arr[80: 88, 0: 32]
    frames[:, 32: 64] = arr[88: 96, 0: 32]
    frames[:, 64: 96] = arr[80: 88, 32: 64]
    frames[:, 96: 128] = arr[88: 96, 32: 64]
    frames[:, 128: 160] = arr[80: 88, 64: 96]
    frames[:, 160: 192] = arr[88: 96, 64: 96]

    frames[:, 192: 224] = arr[96: 104, 0: 32]
    frames[:, 224: 256] = arr[104: 112, 0: 32]
    frames[:, 256: 288] = arr[96: 104, 32: 64]
    frames[:, 288: 320] = arr[104: 112, 32: 64]
    frames[:, 320: 352] = arr[96: 104, 64: 96]
    frames[:, 352: 384] = arr[104: 112, 64: 96]
    
    return portrait, frames, minimug


SEARCH_RANGE = 2, 6
def cv_locate_eye_mouse_pos(arr: numpy.array):
    eye = arr[48: 64, 96: 128]
    mouth = arr[80: 96, 96: 128]
    face = arr[:80, :96]
    min_eye = 0, 0
    min_mouth = 0, 0
    min_eye_diff = 512
    min_mouth_diff = 512
    for i in range(SEARCH_RANGE[0], SEARCH_RANGE[1] + 1):
        for j in range(SEARCH_RANGE[0], SEARCH_RANGE[1] + 1):
            slice = face[8 * i: 8 * i + 16, 8 * j: 8 * j + 32]
            eye_diff = numpy.sum(numpy.sign(numpy.abs(slice - eye)))
            mouth_diff = numpy.sum(numpy.sign(numpy.abs(slice - mouth)))
            if eye_diff < min_eye_diff:
                min_eye = j, i
                min_eye_diff = eye_diff
            if mouth_diff < min_mouth_diff:
                min_mouth = j, i
                min_mouth_diff = mouth_diff
    return min_mouth[0], min_mouth[1], min_eye[0], min_eye[1]


def load_portrait(path: str, file: str, free_space, row: int = -1):
    image_file = f"{path}/{file}.png"
    asset_file = f"{path}/{file}.asset"
    with pyEA.row("PortraitTable", row):
        with open(image_file, "rb") as file:
            crc_image = zlib.crc32(file.read())
        if os.path.isfile(asset_file):
            with open(asset_file, "rb") as file:
                crc = int.from_bytes(file.read(4), "little")
                if crc == crc_image:
                    mouse_eye_pos = file.read(4)
                    buffer = file.read()
                    pos = free_space.tell()
                    with pyEA.alloc(free_space):
                        pyEA.write(buffer)
                    pyEA.write_ptr(pos + 0x1624)
                    pyEA.write_ptr(pos + 0x1604)
                    pyEA.write_ptr(pos + 0x1004)
                    pyEA.write_ptr(0)
                    pyEA.write(mouse_eye_pos)
                    pyEA.write_byte(1)
                    pyEA.write_byte(0, 0, 0)
        image: Image.Image = Image.open(image_file)
        try:
            palette = image.palette.colors
            if len(palette) > 17:
                image = image.quantize(16)
        except AttributeError:
            image = image.quantize(16)
        palette = [i for i in image.palette.colors][:16]
        arr = numpy.array(image.getdata(), dtype='<u1').reshape((112, 128))
        transparent = arr[0][0]
        if transparent != 0:
            palette[0], palette[transparent] = palette[transparent], palette[0]
            arr = arr + (arr == 0) * 20
            arr = arr - (arr == transparent) * transparent
            arr = arr - (arr == 20) * 20
        portrait, frames, minimug = cut_image(arr)

        portrait = HEADER + to_gba(portrait).tobytes()
        frames = to_gba(frames).tobytes()
        minimug = lz77.compress(to_gba(minimug).tobytes())
        palette = palette_to_bytes(palette)

        buffer = portrait + frames + palette + minimug

        x1, y1, x2, y2 = cv_locate_eye_mouse_pos(arr)
        mouse_eye_pos = x1.to_bytes(1, "little") + y1.to_bytes(1, "little") + x2.to_bytes(1, "little") + y2.to_bytes(1, "little")

        pos = free_space.tell()
        with pyEA.alloc(free_space):
            pyEA.write(buffer)
        pyEA.write_ptr(pos + 0x1624)
        pyEA.write_ptr(pos + 0x1604)
        pyEA.write_ptr(pos + 0x1004)
        pyEA.write_ptr(0)
        pyEA.write(mouse_eye_pos)
        pyEA.write_byte(1)
        pyEA.write_byte(0, 0, 0)

        with open(asset_file, "wb") as file:
            file.write(crc_image.to_bytes(4, "little"))
            file.write(mouse_eye_pos)
            file.write(buffer)


