
from typing import *
import pyEA.asm
import pyEA.items
import pyEA.units
import pyEA.classes

ASSET_TYPES: Dict[str, Union[None, Callable[[str, str], bytes]]] = {
    ".dmp": None,
    ".s": pyEA.asm.asm_s_compiler,
    ".asm": pyEA.asm.asm_compiler,
    ".c": pyEA.asm.chax_compiler,
    ".class.json": pyEA.classes.parse_class,
    ".unit.json": pyEA.units.parse_unit,
    ".item.json": pyEA.items.parse_item,
}

