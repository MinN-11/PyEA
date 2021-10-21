
from PIL import Image
import numpy
import lz77
from graphics import to_gba, palette_to_bytes

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


def load_portrait(file: str):
    image: Image.Image = Image.open(file)
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
    minimug = to_gba(minimug).tobytes()

    palette = palette_to_bytes(palette)
    return portrait, frames, palette, lz77.compress(minimug),
