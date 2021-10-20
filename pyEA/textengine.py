
NO_NARROW = 0
NARROW = 1
AUTOMATIC = 2

FIXED = 0
REDO = 1


def to_narrow(char: str):
    return char


def measure_string(string):
    return len(string) * 3


def draw_string(string: str, is_narrow: int = NO_NARROW, line_wrap=FIXED):
    pass