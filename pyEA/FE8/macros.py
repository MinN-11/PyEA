
import pyEA


def macro(func):
    def wrapper(**kwargs):
        kwargs = {key: pyEA.fetch(kwargs[key]) for key in kwargs}
        func(kwargs)
    return wrapper


def requires_align4(func):
    def wrapper(x):
        if not pyEA.is_aligned():
            print(f"Warning: Macro {func.__name__} on a non-4-aligned offset")
        func(x)
    return wrapper


@macro
def B(offset):
    v = ((((offset - pyEA.get_offset() - 4) >> 1) & 0x7ff) | 0xE000)
    pyEA.write_short(v)


@macro
def BL(offset):
    bl_range = (offset - pyEA.get_offset() - 4) >> 1
    v1 = ((bl_range >> 11) & 0x7ff) | 0xf000
    v2 = (bl_range & 0x7ff) | 0xf800
    pyEA.write_short(v1, v2)


@macro
@requires_align4
def jump_to_hack(offset):
    pyEA.write_short(0x4B00, 0x4718)
    pyEA.write_ptr1(offset)


@macro
@requires_align4
def jump_to_hack0(offset):
    pyEA.write_short(0x4800, 0x4700)
    pyEA.write_ptr1(offset)


@macro
@requires_align4
def jump_to_hack1(offset):
    pyEA.write_short(0x4900, 0x4708)
    pyEA.write_ptr1(offset)


@macro
@requires_align4
def jump_to_hack2(offset):
    pyEA.write_short(0x4A00, 0x4710)
    pyEA.write_ptr1(offset)


@macro
@requires_align4
def jump_to_hack3(offset):
    pyEA.write_short(0x4B00, 0x4718)
    pyEA.write_ptr1(offset)


@macro
@requires_align4
def goto(label):
    pass


@macro
@requires_align4
def elabel(label):
    pass