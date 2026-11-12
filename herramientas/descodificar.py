#!/usr/bin/env python3
"""Turn the backup image that the recipe book page stores into its JSON text.

The page saves its data as a PNG asset (format «png-rgb-v1»): the pixels,
read left to right and top to bottom, three bytes each (R, G, B), hold a
4-byte big-endian length followed by that many bytes of UTF-8 JSON.

Usage:
    python3 herramientas/descodificar.py copia.png recetario.json [--sha256 HEX]

With --sha256 the script fails unless the JSON bytes have that SHA-256
(the value the page wrote in the `meta/backup` document, field `hash`).
"""
import hashlib
import json
import struct
import sys
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def png_rgb_bytes(data):
    """Return the image's bytes in R, G, B order, without any alpha channel."""
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file")
    pos, idat, header = 8, [], None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat.append(body)
        pos += 12 + length
    if header is None:
        raise ValueError("PNG without IHDR")
    width, height, depth, color, _, _, interlace = header
    if depth != 8 or color not in (2, 6) or interlace != 0:
        raise ValueError(f"unsupported PNG (depth {depth}, colour type {color}, interlace {interlace})")
    bpp = 3 if color == 2 else 4
    stride = width * bpp
    lines = zlib.decompress(b"".join(idat))
    out = bytearray()
    previous = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind = lines[start]
        row = bytearray(lines[start + 1:start + 1 + stride])
        for i in range(stride):
            left = row[i - bpp] if i >= bpp else 0
            up = previous[i]
            up_left = previous[i - bpp] if i >= bpp else 0
            if kind == 1:
                row[i] = (row[i] + left) & 0xFF
            elif kind == 2:
                row[i] = (row[i] + up) & 0xFF
            elif kind == 3:
                row[i] = (row[i] + ((left + up) >> 1)) & 0xFF
            elif kind == 4:
                row[i] = (row[i] + paeth(left, up, up_left)) & 0xFF
            elif kind != 0:
                raise ValueError(f"unknown PNG filter {kind}")
        if bpp == 3:
            out += row
        else:
            for i in range(0, stride, 4):
                out += row[i:i + 3]
        previous = row
    return bytes(out)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    expected = None
    if "--sha256" in argv:
        expected = argv[argv.index("--sha256") + 1].lower()
        args = [a for a in args if a.lower() != expected]
    if len(args) != 2:
        print(__doc__)
        return 2
    payload = png_rgb_bytes(open(args[0], "rb").read())
    (length,) = struct.unpack(">I", payload[:4])
    text = payload[4:4 + length]
    if len(text) != length:
        print("error: the image is shorter than the length it declares")
        return 1
    digest = hashlib.sha256(text).hexdigest()
    if expected and digest != expected:
        print(f"error: sha256 mismatch (got {digest}, expected {expected})")
        return 1
    json.loads(text.decode("utf-8"))  # fails loudly if it is not valid JSON
    open(args[1], "wb").write(text)
    print(f"{args[1]}: {length} bytes, sha256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
