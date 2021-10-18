
__this = __import__(__name__)


def has_global(name: str):
    return hasattr(__this, name)


def define_global(name: str):
    return setattr(__this, name, None)


def set_global(name: str, value: int):
    return setattr(__this, name, value)


def undef_global(name: str):
    return delattr(__this, name)