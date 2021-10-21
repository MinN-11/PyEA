
from varname import varname
from typing import *
GLOBALS: Dict[str, int] = {}


def define(value: int):
    v = varname()
    GLOBALS[v] = value
    return value


def set(name: str, value: int):
    GLOBALS[name] = value


def exists(value: str):
    return value in GLOBALS
