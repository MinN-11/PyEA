
from typing import *
import pyEA.asm
from pyEA.tables import *
import pyEA.item

ASSET_TYPES: Dict[str, Union[None, Callable[[str, str], bytes]]] = {
    ".dmp": None,
    ".s": pyEA.asm.asm_s_compiler,
    ".asm": pyEA.asm.asm_compiler,
    ".c": pyEA.asm.chax_compiler,
    ".unit": character_compiler,
    ".class": class_compiler,
    ".item": pyEA.item.parse_item,
    ".chapter": chapter_compiler,
}

