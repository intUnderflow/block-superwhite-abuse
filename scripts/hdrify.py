#!/usr/bin/env python3
"""Combine an SDR capture and a "superwhite matte" into an HDR PNG.

Takes two same-sized PNGs: the base image, and a matte that is white
wherever content should glow (soft gray edges blend). The base is encoded
with SDR white at the 203-nit HDR reference; matte-white regions have
their luminance scaled up to 5000 nits — superwhite's own peak. Output is
an RGB (no alpha) PNG with a cICP chunk (BT.2020 primaries, PQ transfer,
9/16/0/1), 16-bit by default or 24-bit ("8") for Chrome Web Store promo
images, which require JPEG or 24-bit PNG. The 8-bit path applies seeded
triangular dither, since PQ at 8 bits would otherwise band in the dark
gradient.

Decoding the input PNGs is delegated to ffmpeg; everything else is
standard library.

Usage: python3 scripts/hdrify.py base.png matte.png out.png [8|16]
"""

import random
import struct
import subprocess
import sys
import zlib

SDR_WHITE_NITS = 203.0
BOOST_NITS = 5000.0
PQ_PEAK_NITS = 10000.0

M2020 = (
    (0.6274, 0.3293, 0.0433),
    (0.0691, 0.9195, 0.0114),
    (0.0164, 0.0880, 0.8956),
)

PQ_M1 = 2610 / 16384
PQ_M2 = 2523 / 4096 * 128
PQ_C1 = 3424 / 4096
PQ_C2 = 2413 / 4096 * 32
PQ_C3 = 2392 / 4096 * 32


def png_size(path):
    with open(path, "rb") as f:
        header = f.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
    return struct.unpack(">II", header[16:24])


def decode_rgb(path):
    """Decode a PNG to raw RGB24 bytes via ffmpeg."""
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"],
        check=True, capture_output=True,
    ).stdout


def pq_encode(nits):
    y = (nits / PQ_PEAK_NITS) ** PQ_M1
    return ((PQ_C1 + PQ_C2 * y) / (1 + PQ_C3 * y)) ** PQ_M2


# sRGB byte -> linear, and a fine-grained PQ table over boosted intensity
# (0..BOOST_NITS) with linear interpolation, to keep the per-pixel loop fast.
SRGB_LUT = [
    (c / 255) / 12.92 if c / 255 <= 0.04045
    else (((c / 255) + 0.055) / 1.055) ** 2.4
    for c in range(256)
]
PQ_STEPS = 4096
PQ_LUT = [pq_encode(BOOST_NITS * i / (PQ_STEPS - 1)) for i in range(PQ_STEPS)]


def pq_fast(nits):
    x = min(max(nits, 0.0), BOOST_NITS) / BOOST_NITS * (PQ_STEPS - 1)
    i = int(x)
    if i >= PQ_STEPS - 1:
        return PQ_LUT[-1]
    frac = x - i
    return PQ_LUT[i] * (1 - frac) + PQ_LUT[i + 1] * frac


def hdrify(base, matte, width, height, bits):
    gain = BOOST_NITS / SDR_WHITE_NITS - 1
    rng = random.Random(0)  # seeded: builds are reproducible
    out = bytearray()
    row_len = width * 3
    for y in range(height):
        out.append(0)  # PNG filter type: None
        row = base[y * row_len:(y + 1) * row_len]
        mrow = matte[y * row_len:(y + 1) * row_len]
        for x in range(width):
            i = x * 3
            r = SRGB_LUT[row[i]]
            g = SRGB_LUT[row[i + 1]]
            b = SRGB_LUT[row[i + 2]]
            boost = 1 + gain * SRGB_LUT[mrow[i]]  # matte is grayscale
            for m in M2020:
                nits = SDR_WHITE_NITS * boost * (
                    m[0] * r + m[1] * g + m[2] * b
                )
                pq = pq_fast(nits)
                if bits == 8:
                    q = pq * 255 + rng.random() + rng.random() - 1
                    out.append(max(0, min(255, round(q))))
                else:
                    out += struct.pack(">H", round(pq * 65535))
    return bytes(out)


def write_png(path, width, height, raw, bits):
    def chunk(tag, data):
        payload = tag + data
        return (
            struct.pack(">I", len(data))
            + payload
            + struct.pack(">I", zlib.crc32(payload))
        )

    ihdr = struct.pack(">IIBBBBB", width, height, bits, 2, 0, 0, 0)  # RGB
    cicp = bytes([9, 16, 0, 1])  # BT.2020 primaries, PQ, RGB, full range
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"cICP", cicp))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


def main():
    base_path, matte_path, out_path = sys.argv[1:4]
    bits = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    assert bits in (8, 16), "bits must be 8 or 16"
    width, height = png_size(base_path)
    assert (width, height) == png_size(matte_path), "size mismatch"
    base, matte = decode_rgb(base_path), decode_rgb(matte_path)
    raw = hdrify(base, matte, width, height, bits)
    write_png(out_path, width, height, raw, bits)
    print(f"wrote {out_path} ({width}x{height}, {bits}-bit)")


if __name__ == "__main__":
    main()
