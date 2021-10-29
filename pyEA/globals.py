
from varname import varname
from typing import *


# define is slow
# to mass convert define to set
# run regex replace
# ([A-Za-z][A-Za-z_0-9.]*) = define\((\d+|0x[0-9a-fA-F]+)\)
# with
# $1 = set("$1", $2)

GLOBALS: Dict[str, int] = {}


def define(value: int):
    v = varname()
    if v in GLOBALS and GLOBALS[v] != value:
        print(f"Warning: resetting global {v} {GLOBALS[v]} to {value}")
    GLOBALS[v] = value
    return value


def set(name: str, value: int):
    if name in GLOBALS and GLOBALS[name] != value:
        print(f"Warning: resetting global {name} {GLOBALS[name]} to {value}")
    GLOBALS[name] = value
    return value


def exists(value: str):
    return value in GLOBALS
