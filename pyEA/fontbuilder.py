from PIL import Image, ImageFont, ImageDraw
import numpy

# image = Image.new("P", (16,16))
# image.show()

font_palette = (104, 136, 168, 168, 168, 168, 248, 248, 248, 40, 40, 40)

charset = [chr(i) for i in range(0x20, 0x7b)]


def glyph_size(arr):
    a = numpy.where((arr != 0).any(0))[0]
    if a.size == 0:
        return 0
    return numpy.max(a) - numpy.min(a)


def segments(arr):
    idx = numpy.where(arr != 0)[0]
    return numpy.size(numpy.where(numpy.diff(idx) != 1))


def narrowify(arr):
    arr = narrowify_pass1(arr)
    arr = narrowify_pass2(arr)
    arr = narrowify_pass3(arr)
    arr = narrowify_pass4(arr)
    arr = narrowify_pass3(arr)
    return arr


def narrowify_pass1(arr):
    builder = numpy.zeros((16, 16), dtype="<u1")
    size = glyph_size(arr)
    if size <= 3:
        return arr
    k = 0
    i = -1
    while i < 14:
        i += 1
        this = arr[:, i]
        next = arr[:, i + 1]
        if size > 3 and numpy.array_equal(this, next):
            size -= 1
            continue
        if numpy.sum(this) == 0:
            builder[:, k] = this
            k += 1
            continue
        builder[:, k] = this
        k += 1
    return builder


def narrowify_pass2(arr):
    builder = numpy.zeros((16, 16), dtype="<u1")
    if glyph_size(arr) <= 3:
        return arr
    k = 0
    i = -1
    while i < 14:
        i += 1
        this = arr[:, i]
        next = arr[:, i + 1]
        if numpy.sum(this) == 0:
            builder[:, k] = this
            k += 1
            continue
        if i != 0:  # if a hole is filled, don't merge
            w = next & arr[:, i - 1]
            if not numpy.array_equal(w, w & this):
                builder[:, k] = this
                k += 1
                continue

        div = numpy.hstack((this - next))
        a = div[1:]
        b = div[:-1]
        c = a + b
        d = numpy.pad(c, (0, 1)) & numpy.pad(c, (1, 0))
        if numpy.sum(d) == 0:
            builder[:, k] = this | next
            i += 1
            k += 1
            continue
        builder[:, k] = this
        k += 1
    return builder


def narrowify_pass3(arr):
    builder = numpy.zeros((16, 16), dtype="<u1")
    if glyph_size(arr) <= 3:
        return arr
    k = 0
    i = -1
    while i < 14:
        i += 1
        this = arr[:, i]
        next = arr[:, i + 1]
        if numpy.sum(this) == 0:
            builder[:, k] = this
            k += 1
            continue
        div = (this - next)
        if numpy.sum(div) == 1:
            builder[:, k] = this | next
            i += 1
            k += 1
            continue
        builder[:, k] = this
        k += 1
    return builder


def narrowify_pass4(arr):
    builder = numpy.zeros((16, 16), dtype="<u1")
    if glyph_size(arr) <= 3:
        return arr
    k = 0
    i = -1
    while i < 14:
        i += 1
        this = arr[:, i]
        next = arr[:, i + 1]
        if numpy.sum(this) == 0:
            builder[:, k] = this
            k += 1
            continue
        if i != 0:  # if a hole is filled, don't merge
            w = next & arr[:, i - 1]
            if not numpy.array_equal(w, w & this):
                builder[:, k] = this
                k += 1
                continue
        if i != 14:  # if a hole is filled, don't merge
            w = this & arr[:, i + 2]
            if not numpy.array_equal(w, w & next):
                builder[:, k] = this
                k += 1
                continue
        join = this | next
        union = this & next
        if segments(this) == segments(next) == segments(join):
            if segments(this - union) == segments(next - union) == segments(join - union):
                builder[:, k] = this | next
                i += 1
                k += 1
                continue
        builder[:, k] = this
        k += 1
    return builder


def serif_font(arr):
    right_shadow = numpy.hstack((numpy.zeros((16, 1), dtype="<u1"), (arr == 3)[:, :15]))
    top = arr[:10, :]
    bot = arr[10:, :]
    top_shadow = numpy.vstack((numpy.zeros((1, 16), dtype="<u1"), (top == 3)[:-1, :]))
    bot_shadow = numpy.vstack(((bot == 3)[1:, :], numpy.zeros((1, 16), dtype="<u1")))

    arr = arr | ((right_shadow | numpy.vstack((top_shadow, bot_shadow))) * 2)

    trim = numpy.where(arr != 0)[1]
    trim = numpy.min(trim) if trim.size > 0 else 0
    return numpy.hstack((arr[:, trim:], numpy.zeros((16, trim), dtype="<u1")))


def menu_font(arr):
    right_shadow = numpy.hstack((numpy.zeros((16, 1), dtype="<u1"), (arr == 3)[:, :-1]))
    top_shadow = numpy.vstack((numpy.zeros((1, 16), dtype="<u1"), (arr == 3)[:-1, :]))
    left_shadow = numpy.hstack(((arr == 3)[:, 1:], (numpy.zeros((16, 1), dtype="<u1"))))
    bot_shadow = numpy.vstack(((arr == 3)[1:, :], (numpy.zeros((1, 16), dtype="<u1"))))

    arr = arr | right_shadow | left_shadow | top_shadow | bot_shadow

    arr = ((arr == 3) * 2) + ((arr == 1) * 3)
    arr = arr.astype("<u1")
    trim = numpy.where(arr != 0)[1]
    trim = numpy.min(trim) if trim.size > 0 else 0
    return numpy.hstack((arr[:, trim:], numpy.zeros((16, trim), dtype="<u1")))


def draw(font, character):
    image: Image.Image = Image.new("P", (16, 16))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), character, 1, font=font)
    return numpy.array(image.getdata(), dtype='<u1').reshape((16, 16))


if __name__ == '__main__':
    buffer = None
    font = ImageFont.truetype("PixelOperator.ttf", 16)
    for i in charset:
        arr = draw(font, i)
        arr2 = narrowify(arr) * 3
        arr3 = menu_font(arr * 3)
        arr4 = menu_font(arr2)
        arr = serif_font(arr * 3)
        arr2 = serif_font(arr2)
        a = numpy.hstack((arr, arr2, arr3, arr4))
        if buffer is None:
            buffer = a
        else:
            buffer = numpy.vstack((buffer, a))

    im2 = Image.fromarray(buffer)
    im2.putpalette(font_palette)
    im2.save("out.png")
    im2.show()

