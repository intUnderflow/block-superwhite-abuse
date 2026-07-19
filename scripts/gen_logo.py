#!/usr/bin/env python3
"""Generate the superwhite HDR logo PNGs.

Yes, really. The red prohibition sign is encoded at normal SDR brightness
(203-nit HDR reference white, ITU-R BT.2408), while the white glare behind
it is encoded at 5000 nits — the same peak brightness superwhite itself
uses. On an HDR display the logo does exactly the thing this extension
blocks; install the extension and it renders as ordinary white. The logo
is its own demo.

Outputs are PNG Third Edition HDR PNGs: 16-bit RGBA with a cICP chunk
declaring BT.2020 primaries / PQ transfer / full-range RGB (9/16/0/1),
supported by current Chrome, Firefox and Safari. SDR displays tone-map
them to a normal-looking logo.

Emits the 512px README logo and a 128px icon-sized variant. The manifest
deliberately keeps the SDR icons (Chrome composites its own UI in SDR).

Pure standard library — no Pillow, no ffmpeg.

Usage: python3 scripts/gen_logo.py
"""

import math
import os
import struct
import zlib

OUTPUTS = [
    (512, "logo-superwhite.png"),
    (128, "icon128-superwhite.png"),
]
SS = 2  # supersampling factor

RED_SRGB = (204 / 255, 32 / 255, 40 / 255)
SDR_WHITE_NITS = 203.0  # HDR reference white (ITU-R BT.2408)
GLARE_NITS = 5000.0  # the peak brightness superwhite uses
PQ_PEAK_NITS = 10000.0

# Linear BT.709/sRGB -> linear BT.2020 (ITU-R BT.2087).
M2020 = (
    (0.6274, 0.3293, 0.0433),
    (0.0691, 0.9195, 0.0114),
    (0.0164, 0.0880, 0.8956),
)

# ITU-R BT.2100 PQ inverse-EOTF constants.
PQ_M1 = 2610 / 16384
PQ_M2 = 2523 / 4096 * 128
PQ_C1 = 3424 / 4096
PQ_C2 = 2413 / 4096 * 32
PQ_C3 = 2392 / 4096 * 32


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def pq_encode(nits):
    y = max(0.0, nits / PQ_PEAK_NITS) ** PQ_M1
    return ((PQ_C1 + PQ_C2 * y) / (1 + PQ_C3 * y)) ** PQ_M2


def smoothstep(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def render(size):
    """Render premultiplied linear BT.2020 RGB in absolute nits, plus alpha."""
    n = size * SS
    c = (n - 1) / 2.0
    ring_outer = 0.46 * n
    ring_thickness = 0.13 * n
    ring_inner = ring_outer - ring_thickness
    glow_core = 0.20 * n
    glow_edge = ring_outer

    lin = srgb_to_linear
    red_lin = (lin(RED_SRGB[0]), lin(RED_SRGB[1]), lin(RED_SRGB[2]))
    red_nits = tuple(
        SDR_WHITE_NITS * sum(M2020[i][j] * red_lin[j] for j in range(3))
        for i in range(3)
    )

    inv_sqrt2 = 1 / math.sqrt(2)
    buf = [[(0.0, 0.0, 0.0, 0.0)] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)

            # Superwhite glare, premultiplied.
            a = 1.0 - smoothstep(glow_core, glow_edge, d)
            r = g = b = GLARE_NITS * a

            # Prohibition sign at civilized SDR brightness.
            in_ring = ring_inner <= d <= ring_outer
            bar_dist = abs(dx * inv_sqrt2 - dy * inv_sqrt2)
            in_bar = bar_dist <= ring_thickness / 2 and d <= ring_outer
            if in_ring or in_bar:
                r, g, b = red_nits
                a = 1.0

            buf[y][x] = (r, g, b, a)
    return buf


def encode_scanlines(buf, size):
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
            for v in (pq_encode(r), pq_encode(g), pq_encode(b), a):
                out += struct.pack(">H", round(max(0.0, min(1.0, v)) * 65535))
    return bytes(out)


def write_png(path, size, raw):
    def chunk(tag, data):
        payload = tag + data
        return (
            struct.pack(">I", len(data))
            + payload
            + struct.pack(">I", zlib.crc32(payload))
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 16, 6, 0, 0, 0)  # 16-bit RGBA
    cicp = bytes([9, 16, 0, 1])  # BT.2020 primaries, PQ, RGB, full range
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"cICP", cicp))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


def main():
    print(f"glare  : {GLARE_NITS:.0f} nits -> PQ {pq_encode(GLARE_NITS):.4f}")
    print(f"SDR ref: {SDR_WHITE_NITS:.0f} nits -> PQ {pq_encode(SDR_WHITE_NITS):.4f}")
    icons_dir = os.path.join(os.path.dirname(__file__), "..", "icons")
    for size, name in OUTPUTS:
        path = os.path.join(icons_dir, name)
        write_png(path, size, encode_scanlines(render(size), size))
        print(f"wrote {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
