READ_AHEAD_BUFFER_SIZE = 0x00000012
SLIDING_WINDOW_SIZE = 0x00001000


def b(v: int):
    return v.to_bytes(1, "little")


def length_of_match(data, x, y):
    """Calculates the number of consecutive characters that are the same starting at x and y in data."""
    for c in range(READ_AHEAD_BUFFER_SIZE):
        if (y + c) >= len(data):
            return c
        if data[x + c] != data[y + c]:
            return c
    return READ_AHEAD_BUFFER_SIZE


def search(data, position):
    length = len(data)
    if (position < 3) or ((length - position) < 3):
        return 0, 0
    result = 0, 0
    for i in range(max(0, position - SLIDING_WINDOW_SIZE), position - 1):
        current = length_of_match(data, i, position)
        if current >= result[0]:
            result = (current, position - i)
    return result


def blocks(data):
    position = 0
    while position < len(data):
        compression_flags = 0
        temp = b''
        for bit in (128, 64, 32, 16, 8, 4, 2, 1):
            if position >= len(data):
                break

            size, where = search(data, position)

            if size > 2:
                temp += b((((size - 3) & 0xF) << 4) + (((where - 1) >> 8) & 0xF))
                temp += b((where - 1) & 0xFF)
                position += size
                compression_flags |= bit
            else:
                temp += b(data[position])
                position += 1

        yield b(compression_flags) + temp


def compress(data):
    l = len(data)

    result = b''.join(
        (b'\x10', b(l & 0xff), b((l >> 8) & 0xff), b((l >> 16) & 0xff)) +
        tuple(blocks(data))
    )

    return result + b'\x00' * (-len(result) % 4)


try:
    import pyfastgbalz77
    compress = lambda x: pyfastgbalz77.compress(x, False)
except ImportError:
    pass
