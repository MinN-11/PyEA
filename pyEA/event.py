import pyEA


def event(func):
    def wrapper():
        pyEA.label(func.__name__)
        func()
        pyEA.NOFADE()
        pyEA.ENDA()
    return wrapper()


def event_fade(func):
    def wrapper():
        pyEA.label(func.__name__)
        func()
        pyEA.FADE()
        pyEA.ENDA()
    return wrapper()
