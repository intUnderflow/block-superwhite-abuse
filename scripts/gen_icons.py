#!/usr/bin/env python3
"""Generate the extension icons (a prohibition sign over a white glare).

Pure standard library — no Pillow required. Renders at 4x and box-downsamples
for antialiasing, then writes RGBA PNGs to icons/.

Usage: python3 scripts/gen_icons.py
"""

import math
import os
import struct
import zlib

SIZES = [16, 32, 48, 128]
SS = 4  # supersampling factor

RED = (204, 32, 40)


def smoothstep(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def render(size):
    n = size * SS
    c = (n - 1) / 2.0
    ring_outer = 0.46 * n
    ring_thickness = 0.13 * n
    ring_inner = ring_outer - ring_thickness
    glow_core = 0.20 * n
    glow_edge = ring_outer

    # Premultiplied RGBA float buffer.
    buf = [[(0.0, 0.0, 0.0, 0.0)] * n for _ in range(n)]

    inv_sqrt2 = 1 / math.sqrt(2)
    for y in range(n):
        for x in range(n):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)

            # White glare blob fading out toward the ring.
            a = 1.0 - smoothstep(glow_core, glow_edge, d)
            r = g = b = a  # premultiplied white

            # Prohibition sign: ring plus a 45° bar (top-left to bottom-right).
            in_ring = ring_inner <= d <= ring_outer
            bar_dist = abs(dx * inv_sqrt2 - dy * inv_sqrt2)
            in_bar = bar_dist <= ring_thickness / 2 and d <= ring_outer
            if in_ring or in_bar:
                sr, sg, sb = (v / 255.0 for v in RED)
                r, g, b, a = sr, sg, sb, 1.0

            buf[y][x] = (r, g, b, a)

    # Box-downsample premultiplied values, then unpremultiply.
    out = bytearray()
    for py in range(size):
        out.append(0)  # PNG filter type: None
        for px in range(size):
            r = g = b = a = 0.0
            for sy in range(SS):
                for sx in range(SS):
                    pr, pg, pb, pa = buf[py * SS + sy][px * SS + sx]
                    r += pr
                    g += pg
                    b += pb
                    a += pa
            r, g, b, a = (v / (SS * SS) for v in (r, g, b, a))
            if a > 0:
                r, g, b = r / a, g / a, b / a
            out.extend(
                round(max(0.0, min(1.0, v)) * 255) for v in (r, g, b, a)
            )
    return bytes(out)


def write_png(path, size, raw):
    def chunk(tag, data):
        payload = tag + data
        return (
            struct.pack(">I", len(data))
            + payload
            + struct.pack(">I", zlib.crc32(payload))
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


def main():
    icons_dir = os.path.join(os.path.dirname(__file__), "..", "icons")
    os.makedirs(icons_dir, exist_ok=True)
    for size in SIZES:
        path = os.path.join(icons_dir, f"icon{size}.png")
        write_png(path, size, render(size))
        print(f"wrote {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
