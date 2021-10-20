
from typing import *
from pyEA.asm import asm_compiler, c2ea_compiler
from pyEA.tables import *

ASSET_TYPES: Dict[str, Union[None, Callable[[bytes], bytes]]] = {
    ".dmp": None,
    ".asm": asm_compiler,
    ".c": c2ea_compiler,
    ".unit": character_compiler(),
    ".class": class_compiler(),
    ".item": item_compiler(),
    ".chapter": chapter_compiler(),
}

