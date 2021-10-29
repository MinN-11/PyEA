
import os
import platform
import zlib
import pathlib
import subprocess

CLIB_PATH = str(pathlib.Path(__file__).parent.resolve()) + "/FE_CLib/"


def asm_compiler(address, file_name, s=False) -> bytes:
    asm_file = f"{address}/{file_name}.{'s' if s else 'asm'}"
    asset_file = f"{address}/{file_name}.asset"
    elf_file = f"{address}/{file_name}.elf"
    dmp_file = f"{address}/{file_name}.dmp"
    with open(asm_file, "rb") as file:
        crc_script = zlib.crc32(file.read())
    if os.path.isfile(asset_file):
        with open(asset_file, "rb") as file:
            crc = int.from_bytes(file.read(4), "little")
            if crc == crc_script:
                return file.read()

    if platform.system() == "Windows":
        path = "C:\\devkitPro\\devkitARM\\bin\\"
    else:
        path = "/opt/devkitpro/devkitARM/bin/"
    os.system(f"{path}\\arm-none-eabi-as -g -mcpu=arm7tdmi -mthumb-interwork {asm_file} -o {elf_file}")
    os.system(f"{path}\\arm-none-eabi-objcopy -S {elf_file} -O binary {dmp_file}")
    os.remove(elf_file)
    with open(dmp_file, "rb") as file:
        buffer = file.read()
    with open(asset_file, "wb") as file:
        file.write(crc_script.to_bytes(4, "little"))
        file.write(buffer)
    os.remove(dmp_file)
    return buffer


def asm_s_compiler(address, file_name):
    return asm_compiler(address, file_name, True)


def chax_compiler(address, file_name) -> bytes:
    c_file = f"{address}/{file_name}.c"
    asset_file = f"{address}/{file_name}.asset"
    object_file = f"{address}/{file_name}.o"
    dmp_file = f"{address}/{file_name}.dmp"

    with open(c_file, "rb") as file:
        crc_script = zlib.crc32(file.read())
    if os.path.isfile(asset_file):
        with open(asset_file, "rb") as file:
            crc = int.from_bytes(file.read(4), "little")
            if crc == crc_script:
                return file.read()

    if platform.system() == "Windows":
        path = "C:\\devkitPro\\devkitARM\\bin\\"
    else:
        path = "/opt/devkitpro/devkitARM/bin/"
    os.system(f"{path}\\arm-none-eabi-gcc -I{CLIB_PATH} -mcpu=arm7tdmi -mthumb -mthumb-interwork -Wall -Os -mtune=arm7tdmi -c {c_file} -o {object_file}")
    os.system(f"{path}\\arm-none-eabi-objcopy -S {object_file} -O binary {dmp_file}")
    os.remove(object_file)
    with open(dmp_file, "rb") as file:
        buffer = file.read()
    with open(asset_file, "wb") as file:
        file.write(crc_script.to_bytes(4, "little"))
        file.write(buffer)
    os.remove(dmp_file)
    return buffer

