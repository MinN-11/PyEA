
import javaobj
import os
import pyEA
import numpy
import struct
import re
from pyEA import lz77
from PIL import Image
import zlib
from pyEA.graphics import to_gba

targets = ["Sword", "Lance", "Axe", "Bow", "Staff", "Magic", "Hand Axe", "Unarmed", "????", "Monster"]
hand_axe_table = [0x28, 0x29, 0x2C]

def serialize_java_obj(obj):
    return b''.join([x.to_bytes(1, 'little', signed=True) for x in (obj.readObject(ignore_remaining_data=True))])


def process_sheets(path, name, weapon):
    frames_path = f'{path}/{name}/{weapon} Frame Data.dmp'
    buffer = numpy.fromfile(frames_path, dtype=numpy.uint32)
    header = struct.pack("<L", ((buffer.shape[0] * 4) << 8) + 0x10)
    pyEA.write(header)
    pyEA.write_byte(0)
    is_pointer = False
    add_zero = False
    for i in buffer:
        if is_pointer:
            pyEA.write_ptr(f"__aa_{name}_{weapon}_{i + 1}")
            is_pointer = False
        elif (i & 0xff000000) == 0x86000000:
            is_pointer = True
            pyEA.write_word(i)
        else:
            pyEA.write_word(i)
        if add_zero:
            add_zero = False
            pyEA.write_byte(0)
        else:
            add_zero = True


def load_sheet(path: str, file: str):
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
    try:
        palette = image.palette.colors
        if len(palette) > 17:
            image = image.quantize(16)
    except AttributeError:
        image = image.quantize(16)
    arr = numpy.array(image.getdata(), dtype='<u1').reshape((64, 264))
    data_arr = arr[:, :256]
    palette_arr = numpy.flip(arr[0:2, 256:264], axis=1).flatten()
    for i, v in enumerate(palette_arr):
        data_arr[data_arr == v] = i + 16
    data_arr -= 16
    buffer = lz77.compress(to_gba(data_arr).tobytes())
    with open(asset_file, "wb") as file:
        file.write(crc_image.to_bytes(4, "little"))
        file.write(buffer)
    return buffer


def load_animations(name, path):
    free_space = pyEA.STREAM
    for weapon in targets:
        pyEA.globals.set(f"{name}{weapon}Anim", pyEA.current_row("AnimTable"))
        bin_file = f"{path}/{name}/{weapon}.bin"
        if not os.path.isfile(bin_file):
            continue
        if weapon != "Hand Axe":
            pyEA.write_byte(targets.index(weapon), 1)
            pyEA.write_short(pyEA.current_row("AnimTable"))
        else:
            for axe in hand_axe_table:
                pyEA.write_byte(axe, 0)
                pyEA.write_short(pyEA.current_row("AnimTable"))
        with pyEA.row("AnimTable"):
            with open(bin_file, 'rb') as file:
                obj = javaobj.JavaObjectUnmarshaller(file)
                _ = obj.readObject(ignore_remaining_data=True).path
                sheets_obj_list = obj.readObject(ignore_remaining_data=True).annotations
                _ = sheets_obj_list.pop(0)
                sheet_paths = [x.path for x in sheets_obj_list]
                _ = obj.readObject(ignore_remaining_data=True).annotations
                section_data = serialize_java_obj(obj)
                rtl = lz77.compress(serialize_java_obj(obj))
                ltr = lz77.compress(serialize_java_obj(obj))
                palette = serialize_java_obj(obj)
                palette_data = lz77.compress(palette)

            # trying to put a name here
            name_buffer = (name[:8] + "_" + weapon[:2] + "\0").encode("ascii")
            if len(name_buffer) < 12:
                name_buffer += b'\0' * (12 - len(name_buffer))
            if len(name_buffer) > 12:
                name_buffer = name_buffer[:11] + b'\0'
            pyEA.write(name_buffer)

            with pyEA.alloc(free_space):
                pyEA.write(section_data)
            with pyEA.alloc(free_space):
                process_sheets(path, name, weapon)
            with pyEA.alloc(free_space):
                pyEA.write(rtl)
            with pyEA.alloc(free_space):
                pyEA.write(ltr)
            with pyEA.alloc(free_space):
                pyEA.write(palette_data)
            for sheet in sheet_paths:
                match = re.search(r"Sheet (\d+)\.png", sheet)
                index = int(match.group(1))
                with pyEA.alloc(free_space):
                    pyEA.label(f"__aa_{name}_{weapon}_{index}")
                    pyEA.write(load_sheet(f"{path}/{name}", sheet[:-4]))
    pyEA.write_word(0)
