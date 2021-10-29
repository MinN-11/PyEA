
import pyEA.globals as globals


def load_ea_definitions(file):
    with open(file, "r") as f:
        buffer = f.read()
    for line in buffer.split("\n"):
        split = line.split()
        if len(split) == 3:
            if split[0] != "#define":
                continue
            try:
                num = int(split[2], 0)
            except ValueError:
                continue
            globals.set(split[1], num)
