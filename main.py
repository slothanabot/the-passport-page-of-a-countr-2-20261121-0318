#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws an open passport spread for the island Sultanate of Kalypsis
(capital Port Selene): a data page with a drawn portrait and an MRZ strip,
and a facing page of arrival/departure stamps from the neighbouring
countries Thessaly and Corvina, plus a harbour-tax fee stamp.

Pure Python standard library only: os, struct, zlib, random, math.
No third-party imports, no external fonts or images. The bitmap font
below is hand-drawn, the PNG encoder is written by hand (struct + zlib).
Deterministic: fixed seed, no randomness in layout, no network.
Writes one PNG to /output/entry.png (or $OUTPUT_PATH).
"""
import math
import os
import random
import struct
import zlib

W, H = 1024, 768
OUT = os.environ.get("OUTPUT_PATH", "/output/entry.png")

# ---------------------------------------------------------------- palette
DESK = (20, 52, 58)          # deep teal desk / cover edge
PAPER = (243, 234, 211)      # aged paper
PAPER_DARK = (228, 216, 186)
INK = (28, 32, 40)           # near-black ink
INK_SOFT = (74, 74, 66)
RULE = (120, 100, 60)
GOLD = (158, 118, 40)
TEAL = (18, 90, 92)
SKIN = (232, 184, 143)
SKIN_DARK = (205, 155, 115)
HAIR = (58, 40, 26)
STAMP_BLUE = (32, 74, 138)
STAMP_RED = (158, 44, 44)
STAMP_PURPLE = (104, 62, 140)
FEE_INK = (146, 52, 34)


# ---------------------------------------------------------------- canvas
class Canvas:
    """RGB pixel buffer with simple drawing primitives."""

    def __init__(self, w, h, fill=(0, 0, 0)):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill(fill)

    def fill(self, color):
        r, g, b = color
        self.buf[:] = bytes((r, g, b)) * (self.w * self.h)

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def blend(self, x, y, color, alpha):
        """Alpha-blend an RGB colour over the pixel (alpha 0..255)."""
        if 0 <= x < self.w and 0 <= y < self.h and alpha > 0:
            i = (y * self.w + x) * 3
            a = alpha / 255.0
            for k in range(3):
                self.buf[i + k] = int(self.buf[i + k] * (1 - a)
                                      + color[k] * a + 0.5)

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return self.buf[i], self.buf[i + 1], self.buf[i + 2]

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w - 1, x1)
        y1 = min(self.h - 1, y1)
        row = bytes(color) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            i = (y * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def rect_outline(self, x0, y0, x1, y1, color, width=1):
        for t in range(width):
            self.fill_rect(x0 + t, y0 + t, x1 - t, y0 + t, color)
            self.fill_rect(x0 + t, y1 - t, x1 - t, y1 - t, color)
            self.fill_rect(x0 + t, y0 + t, x0 + t, y1 - t, color)
            self.fill_rect(x1 - t, y0 + t, x1 - t, y1 - t, color)

    def hline(self, x0, x1, y, color, width=1):
        for t in range(width):
            self.fill_rect(x0, y + t, x1, y + t, color)

    def vline(self, x, y0, y1, color, width=1):
        for t in range(width):
            self.fill_rect(x + t, y0, x + t, y1, color)

    def _dot(self, cx, cy, r, color):
        if r <= 0:
            self.put(cx, cy, color)
            return
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.fill_rect(cx - dx, cy + dy, cx + dx, cy + dy, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        """Bresenham line; width>1 stamps discs along it."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        r = width // 2
        while True:
            self._dot(x, y, r, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def polyline(self, pts, color, width=1):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0],
                      pts[i + 1][1], color, width)

    def ellipse_fill(self, x0, y0, x1, y1, color):
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if rx <= 0 or ry <= 0:
            return
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            t = (y - cy) / ry
            if abs(t) > 1:
                continue
            dx = int(rx * math.sqrt(1 - t * t))
            self.fill_rect(int(cx - dx), y, int(cx + dx), y, color)

    def ellipse_outline(self, x0, y0, x1, y1, color, width=1):
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if rx <= 0 or ry <= 0:
            return
        steps = max(48, int(2 * math.pi * max(rx, ry)))
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self._dot(int(cx + rx * math.cos(a)),
                      int(cy + ry * math.sin(a)), width // 2, color)

    def arc(self, x0, y0, x1, y1, a0_deg, a1_deg, color, width=1):
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        steps = max(16, int(abs(a1_deg - a0_deg) / 360.0
                             * 2 * math.pi * max(rx, ry)))
        for i in range(steps + 1):
            a = math.radians(a0_deg + (a1_deg - a0_deg) * i / steps)
            self._dot(int(cx + rx * math.cos(a)),
                      int(cy + ry * math.sin(a)), width // 2, color)

    def polygon_fill(self, pts, color):
        """Scanline fill of a simple polygon."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, int(min(ys))),
                       min(self.h - 1, int(max(ys))) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(math.ceil(xs[i])), y,
                               int(math.floor(xs[i + 1])), y, color)


class Layer:
    """RGBA buffer used for stamps / watermarks, then rotated onto canvas."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 4)

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 4
            r, g, b = color[0], color[1], color[2]
            a = color[3] if len(color) > 3 else 255
            self.buf[i:i + 4] = bytes((r, g, b, a))

    def fill_rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                self.put(x, y, color)

    def rect_outline(self, x0, y0, x1, y1, color, width=1):
        for t in range(width):
            self.fill_rect(x0 + t, y0 + t, x1 - t, y0 + t, color)
            self.fill_rect(x0 + t, y1 - t, x1 - t, y1 - t, color)
            self.fill_rect(x0 + t, y0 + t, x0 + t, y1 - t, color)
            self.fill_rect(x1 - t, y0 + t, x1 - t, y1 - t, color)

    def ellipse_outline(self, x0, y0, x1, y1, color, width=1):
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        steps = max(48, int(2 * math.pi * max(rx, ry)))
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.put(int(cx + rx * math.cos(a)),
                     int(cy + ry * math.sin(a)), color)


def blit_rotated(dst, layer, cx, cy, angle_deg):
    """Paste an RGBA layer onto an RGB canvas, rotated about (cx, cy)."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    corners = [(-layer.w / 2, -layer.h / 2), (layer.w / 2, -layer.h / 2),
               (layer.w / 2, layer.h / 2), (-layer.w / 2, layer.h / 2)]
    rot = [(x * ca - y * sa, x * sa + y * ca) for x, y in corners]
    minx = int(cx + min(p[0] for p in rot)) - 1
    maxx = int(cx + max(p[0] for p in rot)) + 1
    miny = int(cy + min(p[1] for p in rot)) - 1
    maxy = int(cy + max(p[1] for p in rot)) + 1
    for y in range(max(0, miny), min(dst.h - 1, maxy) + 1):
        for x in range(max(0, minx), min(dst.w - 1, maxx) + 1):
            dx, dy = x - cx, y - cy
            # inverse rotation back into layer space
            sx = dx * ca + dy * sa + layer.w / 2
            sy = -dx * sa + dy * ca + layer.h / 2
            ix, iy = int(sx), int(sy)
            if 0 <= ix < layer.w and 0 <= iy < layer.h:
                i = (iy * layer.w + ix) * 4
                al = layer.buf[i + 3]
                if al:
                    dst.blend(x, y, (layer.buf[i], layer.buf[i + 1],
                                     layer.buf[i + 2]), al)

# ---------------------------------------------------------------- bitmap font
# Hand-drawn 5x7 glyphs: each glyph is 7 rows of 5 cells, '#' = ink.
GLYPHS = {
    "A": ".###./#...#/#...#/#####/#...#/#...#/#...#",
    "B": "####./#...#/#...#/####./#...#/#...#/####.",
    "C": ".####/#..../#..../#..../#..../#..../.####",
    "D": "####./#...#/#...#/#...#/#...#/#...#/####.",
    "E": "#####/#..../#..../####./#..../#..../#####",
    "F": "#####/#..../#..../####./#..../#..../#....",
    "G": ".####/#..../#..../#.###/#...#/#...#/.###.",
    "H": "#...#/#...#/#...#/#####/#...#/#...#/#...#",
    "I": ".###./..#../..#../..#../..#../..#../.###.",
    "J": "..###/...#./...#./...#./...#./#..#./.##..",
    "K": "#...#/#..#./#.#../##.../#.#../#..#./#...#",
    "L": "#..../#..../#..../#..../#..../#..../#####",
    "M": "#...#/##.##/#.#.#/#.#.#/#...#/#...#/#...#",
    "N": "#...#/##..#/##..#/#.#.#/#..##/#..##/#...#",
    "O": ".###./#...#/#...#/#...#/#...#/#...#/.###.",
    "P": "####./#...#/#...#/####./#..../#..../#....",
    "Q": ".###./#...#/#...#/#...#/#.#.#/#..#./.##.#",
    "R": "####./#...#/#...#/####./#.#../#..#./#...#",
    "S": ".####/#..../#..../.###./....#/....#/####.",
    "T": "#####/..#../..#../..#../..#../..#../..#..",
    "U": "#...#/#...#/#...#/#...#/#...#/#...#/.###.",
    "V": "#...#/#...#/#...#/#...#/#...#/.#.#./..#..",
    "W": "#...#/#...#/#...#/#.#.#/#.#.#/##.##/#...#",
    "X": "#...#/#...#/.#.#./..#../.#.#./#...#/#...#",
    "Y": "#...#/#...#/.#.#./..#../..#../..#../..#..",
    "Z": "#####/....#/...#./..#../.#.../#..../#####",
    "0": ".###./#...#/#..##/#.#.#/##..#/#...#/.###.",
    "1": "..#../.##../..#../..#../..#../..#../.###.",
    "2": ".###./#...#/....#/...#./..#../.#.../#####",
    "3": "####./....#/....#/.###./....#/....#/####.",
    "4": "...#./..##./.#.#./#..#./#####/...#./...#.",
    "5": "#####/#..../####./....#/....#/#...#/.###.",
    "6": ".###./#..../#..../####./#...#/#...#/.###.",
    "7": "#####/....#/...#./..#../.#.../.#.../.#...",
    "8": ".###./#...#/#...#/.###./#...#/#...#/.###.",
    "9": ".###./#...#/#...#/.####/....#/....#/.###.",
    " ": "...../...../...../...../...../...../.....",
    ".": "...../...../...../...../...../.##../.##..",
    ",": "...../...../...../...../...../.##../.#...",
    "'": "..#../..#../.#.../...../...../...../.....",
    "\u2019": "..#../..#../.#.../...../...../...../.....",
    "-": "...../...../...../#####/...../...../.....",
    "\u2014": "...../...../...../#####/#####/...../.....",
    "\u00b7": "...../...../...../.##../.##../...../.....",
    "<": "...#./..#../.#.../#..../.#.../..#../...#.",
    ">": ".#.../..#../...#./....#/..#../...#./.#...",
    "(": "...#./..#../.#.../.#.../.#.../..#../...#.",
    ")": ".#.../..#../...#./...#./...#./..#../.#...",
    "/": "....#/....#/...#./..#../.#.../#..../#....",
    ":": "...../.##../.##../...../.##../.##../.....",
    ";": "...../.##../.##../...../.##../.##../.#...",
    "!": "..#../..#../..#../..#../..#../...../..#..",
    "&": ".##../#..#./#..#./.#.../#.#.#/#..#./.##.#",
    "+": "...../..#../..#../#####/..#../..#../.....",
    "%": "#...#/#..#./...#./..#../.#.../#..#./#...#",
    '"': ".#.#./.#.#./...../...../...../...../.....",
    "?": ".###./#...#/....#/..#../..#../...../..#..",
    "=": "...../...../#####/...../#####/...../.....",
    "_": "...../...../...../...../...../...../#####",
    "*": "...../.#.#./.###./#####/.###./.#.#./.....",
}
_BLANK = (".....",) * 7
FONT = {ch: tuple(rows.split("/")) for ch, rows in GLYPHS.items()}


def text_width(s, scale=1, spacing=1):
    if not s:
        return 0
    return len(s) * (5 * scale + spacing) - spacing


def draw_text(cv, x, y, s, color, scale=1, spacing=1, anchor="la"):
    """Draw text on a Canvas or Layer. anchor: la/ma/ra, y is the top."""
    if anchor == "ma":
        x -= text_width(s, scale, spacing) // 2
    elif anchor == "ra":
        x -= text_width(s, scale, spacing)
    cx = x
    for ch in s:
        rows = FONT.get(ch.upper() if ch.isalpha() else ch, _BLANK)
        for gy, row in enumerate(rows):
            for gx, cell in enumerate(row):
                if cell == "#":
                    if scale == 1:
                        cv.put(cx + gx, y + gy, color)
                    else:
                        for sy in range(scale):
                            for sx in range(scale):
                                cv.put(cx + gx * scale + sx,
                                       y + gy * scale + sy, color)
        cx += 5 * scale + spacing


def text_size(sz):
    """Map an old point size to a bitmap scale (glyph is 7 px tall)."""
    return max(1, int(round(sz / 7.0)))


def text(cv, x, y, s, size, color, anchor="la", spacing=1):
    draw_text(cv, x, y, s, color, scale=text_size(size),
              spacing=spacing, anchor=anchor)


# ---------------------------------------------------------------- PNG encoder
def _crc(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", _crc(kind + data)))


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def encode_png(cv):
    """Encode an RGB Canvas as PNG bytes; per-row best filter."""
    w, h = cv.w, cv.h
    raw = bytearray()
    prev = bytearray(w * 3)
    for y in range(h):
        row = cv.buf[y * w * 3:(y + 1) * w * 3]
        best = None
        for ftype in (0, 1, 2, 3, 4):
            filt = bytearray(w * 3)
            for i in range(w * 3):
                a = row[i - 3] if i >= 3 else 0
                b = prev[i]
                c = prev[i - 3] if i >= 3 else 0
                v = row[i]
                if ftype == 0:
                    fv = v
                elif ftype == 1:
                    fv = (v - a) & 0xFF
                elif ftype == 2:
                    fv = (v - b) & 0xFF
                elif ftype == 3:
                    fv = (v - (a + b) // 2) & 0xFF
                else:
                    fv = (v - _paeth(a, b, c)) & 0xFF
                filt[i] = fv
            score = sum((b if b < 128 else 256 - b) for b in filt)
            if best is None or score < best[0]:
                best = (score, ftype, filt)
        raw.append(best[1])
        raw += best[2]
        prev = row
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    return png

# ---------------------------------------------------------------- MRZ
def mrz_check(s):
    vals = {str(i): i for i in range(10)}
    for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        vals[c] = 10 + i
    vals["<"] = 0
    total = 0
    for i, ch in enumerate(s):
        total += vals[ch] * (7, 3, 1)[i % 3]
    return str(total % 10)


def mrz_lines():
    line1 = "P<KLYSELENE<<MARA<ELENI"
    line1 = line1 + "<" * (44 - len(line1))
    doc = "KLY048177"
    dob = "910314"
    exp = "330604"
    personal = "PORTSELENE<<<<"
    line2 = (doc + mrz_check(doc) + "KLY" + dob + mrz_check(dob)
             + "F" + exp + mrz_check(exp) + personal)
    line2 = line2 + mrz_check(line2)
    line2 = line2 + "<" * (44 - len(line2))
    return line1, line2


# ---------------------------------------------------------------- portrait
def draw_portrait(cv, x0, y0, x1, y1):
    """Stylised dignified bust of Mara Eleni Selene, drawn with shapes."""
    pw = x1 - x0
    ph = y1 - y0
    # backdrop: soft vertical gradient, teal sea-green
    for i in range(ph):
        t = i / ph
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((126, 168, 158), (62, 104, 96)))
        cv.fill_rect(x0, y0 + i, x1, y0 + i, c)
    cx = x0 + pw * 0.50
    # shoulders / garment: deep teal robe with gold collar
    cv.polygon_fill([(x0 + pw * 0.10, y1), (x0 + pw * 0.30, y0 + ph * 0.74),
                     (x0 + pw * 0.70, y0 + ph * 0.74),
                     (x0 + pw * 0.90, y1)], (16, 74, 76))
    cv.polygon_fill([(x0 + pw * 0.38, y0 + ph * 0.78),
                     (x0 + pw * 0.50, y0 + ph * 0.86),
                     (x0 + pw * 0.62, y0 + ph * 0.78),
                     (x0 + pw * 0.50, y0 + ph * 0.72)], GOLD)
    # small crescent brooch
    cv.ellipse_fill(int(cx - pw * 0.04), int(y0 + ph * 0.88),
                    int(cx + pw * 0.04), int(y0 + ph * 0.96), GOLD)
    cv.ellipse_fill(int(cx - pw * 0.025), int(y0 + ph * 0.885),
                    int(cx + pw * 0.04), int(y0 + ph * 0.955),
                    (16, 74, 76))
    # neck
    cv.fill_rect(int(cx - pw * 0.055), int(y0 + ph * 0.62),
                 int(cx + pw * 0.055), int(y0 + ph * 0.76), SKIN_DARK)
    # head
    cv.ellipse_fill(int(cx - pw * 0.155), int(y0 + ph * 0.10),
                    int(cx + pw * 0.155), int(y0 + ph * 0.62), SKIN)
    # ears
    cv.ellipse_fill(int(cx - pw * 0.185), int(y0 + ph * 0.33),
                    int(cx - pw * 0.13), int(y0 + ph * 0.45), SKIN)
    cv.ellipse_fill(int(cx + pw * 0.13), int(y0 + ph * 0.33),
                    int(cx + pw * 0.185), int(y0 + ph * 0.45), SKIN)
    # hair: dark mass over the crown, parted centre, bun at the back
    cv.ellipse_fill(int(cx - pw * 0.175), int(y0 + ph * 0.02),
                    int(cx + pw * 0.175), int(y0 + ph * 0.34), HAIR)
    cv.ellipse_fill(int(cx - pw * 0.175), int(y0 + ph * 0.06),
                    int(cx - pw * 0.06), int(y0 + ph * 0.34), HAIR)
    cv.ellipse_fill(int(cx + pw * 0.06), int(y0 + ph * 0.06),
                    int(cx + pw * 0.175), int(y0 + ph * 0.34), HAIR)
    cv.ellipse_fill(int(cx + pw * 0.10), int(y0 + ph * 0.02),
                    int(cx + pw * 0.22), int(y0 + ph * 0.20), HAIR)
    cv.ellipse_outline(int(cx + pw * 0.10), int(y0 + ph * 0.02),
                       int(cx + pw * 0.22), int(y0 + ph * 0.20),
                       (30, 20, 12), width=2)
    # brows, eyes, nose, lips — simple, calm, front-facing
    cv.line(int(cx - pw * 0.105), int(y0 + ph * 0.335),
            int(cx - pw * 0.035), int(y0 + ph * 0.325), HAIR, width=2)
    cv.line(int(cx + pw * 0.035), int(y0 + ph * 0.325),
            int(cx + pw * 0.105), int(y0 + ph * 0.335), HAIR, width=2)
    cv.ellipse_fill(int(cx - pw * 0.095), int(y0 + ph * 0.345),
                    int(cx - pw * 0.045), int(y0 + ph * 0.375),
                    (40, 28, 20))
    cv.ellipse_fill(int(cx + pw * 0.045), int(y0 + ph * 0.345),
                    int(cx + pw * 0.095), int(y0 + ph * 0.375),
                    (40, 28, 20))
    cv.line(int(cx), int(y0 + ph * 0.38),
            int(cx - pw * 0.008), int(y0 + ph * 0.47), SKIN_DARK, width=2)
    cv.line(int(cx - pw * 0.045), int(y0 + ph * 0.505),
            int(cx + pw * 0.045), int(y0 + ph * 0.505),
            (150, 80, 70), width=3)
    # cheek shading
    cv.ellipse_fill(int(cx - pw * 0.13), int(y0 + ph * 0.42),
                    int(cx - pw * 0.06), int(y0 + ph * 0.48),
                    (226, 168, 128))
    cv.ellipse_fill(int(cx + pw * 0.06), int(y0 + ph * 0.42),
                    int(cx + pw * 0.13), int(y0 + ph * 0.48),
                    (226, 168, 128))


def draw_arms(cv, cx, cy, r):
    """Coat of arms: gold disc, crescent moon, star, three waves."""
    cv.ellipse_outline(cx - r, cy - r, cx + r, cy + r, GOLD, width=2)
    cv.ellipse_fill(int(cx - r * 0.55), int(cy - r * 0.55),
                    int(cx + r * 0.55), int(cy + r * 0.55), GOLD)
    cv.ellipse_fill(int(cx - r * 0.28), int(cy - r * 0.55),
                    int(cx + r * 0.72), int(cy + r * 0.45), PAPER)
    # star
    sx, sy = cx + r * 0.28, cy - r * 0.28
    cv.polygon_fill([(int(sx), int(sy - 7)), (int(sx + 2), int(sy - 2)),
                     (int(sx + 7), int(sy)), (int(sx + 2), int(sy + 2)),
                     (int(sx), int(sy + 7)), (int(sx - 2), int(sy + 2)),
                     (int(sx - 7), int(sy)), (int(sx - 2), int(sy - 2))],
                    GOLD)
    # waves
    for wy in (cy + r * 0.62, cy + r * 0.74):
        cv.arc(int(cx - r * 0.8), int(wy - 5), int(cx + r * 0.8),
               int(wy + 5), 180, 360, TEAL, width=2)


# ---------------------------------------------------------------- stamps
def make_stamp(kind, lines, ink, angle, w, h):
    """Build an RGBA stamp layer, then rotate it by angle degrees."""
    layer = Layer(w, h)
    lw = 3
    if kind == "circle":
        layer.ellipse_outline(lw, lw, w - lw, h - lw, ink + (230,),
                              width=lw)
        layer.ellipse_outline(7, 7, w - 7, h - 7, ink + (230,), width=2)
    elif kind == "oval":
        layer.ellipse_outline(lw, lw, w - lw, h - lw, ink + (230,),
                              width=lw)
        layer.ellipse_outline(6, 6, w - 6, h - 6, ink + (230,), width=2)
    else:  # rectangle
        layer.rect_outline(lw, lw, w - lw, h - lw, ink + (230,), width=lw)
        layer.rect_outline(6, 6, w - 6, h - 6, ink + (230,), width=2)
    n = len(lines)
    for i, (s, size, col) in enumerate(lines):
        y = h // 2 + int((i - (n - 1) / 2) * 16) - 7
        draw_text(layer, w // 2, y, s, col + (235,),
                  scale=text_size(size), anchor="ma")
    return layer


def paste_stamp(cv, layer, x, y, angle):
    blit_rotated(cv, layer, x + layer.w // 2, y + layer.h // 2, angle)

# ---------------------------------------------------------------- build
def paper_noise(cv, seed=42):
    """Deterministic faint ageing: speckles and a soft vignette."""
    rng = random.Random(seed)
    for _ in range(2600):
        x = rng.randrange(cv.w)
        y = rng.randrange(cv.h)
        v = rng.randrange(-14, 10)
        r, g, b = cv.get(x, y)
        cv.put(x, y, (max(0, min(255, r + v)),
                      max(0, min(255, g + v)),
                      max(0, min(255, b + v))))
    # vignette: darken a 26 px border band slightly
    for y in range(cv.h):
        for x in range(cv.w):
            d = min(x, cv.w - 1 - x, y, cv.h - 1 - y)
            if d < 26:
                f = (26 - d) / 26.0 * 0.10
                r, g, b = cv.get(x, y)
                cv.put(x, y, (int(r + (120 - r) * f),
                              int(g + (100 - g) * f),
                              int(b + (60 - b) * f)))


def build():
    cv = Canvas(W, H, DESK)

    # ---- spread: two paper pages with a gutter
    x0, y0, x1, y1 = 36, 28, 988, 740
    mid = (x0 + x1) / 2
    cv.fill_rect(x0, y0, x1, y1, PAPER)
    cv.fill_rect(x0, y0, x1, y0 + 4, PAPER_DARK)
    cv.fill_rect(x0, y1 - 4, x1, y1, PAPER_DARK)
    # gutter shadow
    for i in range(14):
        a = 46 - i * 3
        t = max(a, 0) / 255.0
        c = tuple(int(PAPER[k] + (90 - PAPER[k]) * t) if k == 0 else
                  int(PAPER[k] + (70 - PAPER[k]) * t) if k == 1 else
                  int(PAPER[k] + (40 - PAPER[k]) * t) for k in range(3))
        cv.vline(int(mid - 7 + i), y0, y1, c)
    cv.vline(int(mid), y0, y1, (150, 125, 85))
    # perforated passport number along the top edge of the spread
    for i in range(17):
        draw_text(cv, x0 + 14 + i * 54, y0 + 8, "KLY048177",
                  (140, 115, 75), scale=1)

    # faint watermark on both pages
    for wx in (274, 750):
        wm = Layer(400, 90)
        draw_text(wm, 200, 8, "KALYPSIS", (150, 120, 60, 28),
                  scale=9, anchor="ma")
        blit_rotated(cv, wm, wx, 430, -24)

    # ================================================= LEFT PAGE: data page
    cxL = 274
    draw_arms(cv, 96, 66, 16)
    draw_text(cv, cxL, 46, "SULTANATE OF KALYPSIS", INK, scale=2,
              anchor="ma")
    text(cv, cxL, 72, "PASSPORT  \u00b7  PASSEPORT", 12, INK_SOFT,
         anchor="ma")
    cv.hline(66, 482, 94, RULE)
    cv.hline(66, 482, 97, RULE)

    # portrait
    cv.rect_outline(66, 116, 206, 296, INK, width=1)
    cv.rect_outline(70, 120, 202, 292, RULE, width=1)
    draw_portrait(cv, 71, 121, 201, 291)
    text(cv, 136, 300, "PHOTOGRAPH OF HOLDER", 7, INK_SOFT, anchor="ma")

    # data fields, right of the portrait
    fx = 224
    rows = [
        ("TYPE", "P", "CODE", "KLY", "No.", "KLY048177"),
        ("SURNAME", "SELENE", None, None, None, None),
        ("GIVEN NAMES", "MARA ELENI", None, None, None, None),
        ("NATIONALITY", "KALYPSIAN", None, None, None, None),
        ("DATE OF BIRTH", "14 MAR 1991", None, None, None, None),
        ("PLACE OF BIRTH", "PORT SELENE", None, None, None, None),
        ("SEX", "F", None, None, None, None),
        ("DATE OF ISSUE", "04 JUN 2023", None, None, None, None),
        ("DATE OF EXPIRY", "04 JUN 2033", None, None, None, None),
        ("AUTHORITY", "MINISTRY OF THE HARBOUR", None, None, None, None),
    ]
    y = 118
    for row in rows:
        label, value = row[0], row[1]
        text(cv, fx, y, label, 8, INK_SOFT)
        if row[2] is None:
            text(cv, fx, y + 11, value, 13, INK)
            y += 30
        else:
            text(cv, fx, y + 11, value, 13, INK)
            text(cv, fx + 62, y, row[2], 8, INK_SOFT)
            text(cv, fx + 62, y + 11, row[3], 13, INK)
            text(cv, fx + 128, y, row[4], 8, INK_SOFT)
            text(cv, fx + 128, y + 11, row[5], 13, INK)
            y += 30
    # signature
    sy = y + 4
    text(cv, fx, sy, "HOLDER'S SIGNATURE", 8, INK_SOFT)
    cv.hline(fx, fx + 200, sy + 26, INK)
    cv.polyline([(fx + 6, sy + 26), (fx + 40, sy + 14),
                 (fx + 70, sy + 28), (fx + 100, sy + 16),
                 (fx + 130, sy + 27), (fx + 160, sy + 18),
                 (fx + 190, sy + 25)], (30, 40, 90), width=2)

    # MRZ strip
    mrz_y = 640
    cv.fill_rect(56, mrz_y - 12, 492, mrz_y + 46, (238, 228, 200))
    cv.hline(56, 492, mrz_y - 12, INK)
    l1, l2 = mrz_lines()
    draw_text(cv, 66, mrz_y - 4, l1, INK, scale=1, spacing=2)
    draw_text(cv, 66, mrz_y + 16, l2, INK, scale=1, spacing=2)
    text(cv, 482, 716, "1", 11, INK_SOFT, anchor="ra")

    # ================================================= RIGHT PAGE: visas
    cxR = 750
    draw_text(cv, cxR, 46, "VISAS", INK, scale=2, anchor="ma")
    text(cv, cxR, 72, "VISA  \u00b7  ENTRY AND EXIT STAMPS", 11, INK_SOFT,
         anchor="ma")
    cv.hline(542, 958, 94, RULE)
    cv.hline(542, 958, 97, RULE)

    stamps = [
        # (kind, x, y, w, h, angle, ink, lines)
        ("oval", 556, 116, 190, 74, -7, STAMP_BLUE, [
            ("THESSALY", 11, STAMP_BLUE),
            ("ARRIVAL  \u00b7  12 SEP 2023", 9, STAMP_BLUE),
            ("PORT OF VOLOS", 8, STAMP_BLUE)]),
        ("rect", 772, 122, 170, 62, 5, STAMP_BLUE, [
            ("THESSALY \u2014 DEPARTURE", 9, STAMP_BLUE),
            ("26 SEP 2023 \u00b7 VOLOS", 9, STAMP_BLUE)]),
        ("circle", 556, 224, 120, 120, 9, STAMP_RED, [
            ("CORVINA", 11, STAMP_RED),
            ("ARRIVAL", 10, STAMP_RED),
            ("08 FEB 2024", 10, STAMP_RED),
            ("\u00b7 RIVA \u00b7", 8, STAMP_RED)]),
        ("rect", 716, 252, 210, 62, -5, STAMP_RED, [
            ("CORVINA \u2014 DEPARTURE", 9, STAMP_RED),
            ("19 FEB 2024 \u00b7 RIVA HARBOUR", 8, STAMP_RED)]),
        ("oval", 556, 372, 190, 74, 6, STAMP_PURPLE, [
            ("THESSALY", 11, STAMP_PURPLE),
            ("ARRIVAL  \u00b7  03 MAY 2025", 9, STAMP_PURPLE),
            ("PORT OF VOLOS", 8, STAMP_PURPLE)]),
        ("circle", 786, 372, 120, 120, -9, STAMP_PURPLE, [
            ("CORVINA", 11, STAMP_PURPLE),
            ("ARRIVAL", 10, STAMP_PURPLE),
            ("14 AUG 2025", 10, STAMP_PURPLE),
            ("\u00b7 RIVA \u00b7", 8, STAMP_PURPLE)]),
    ]
    for kind, x, y, w, h, ang, ink, lines in stamps:
        layer = make_stamp(kind, lines, ink, ang, w, h)
        paste_stamp(cv, layer, x, y, ang)

    # ---- the telling paperwork detail: harbour-tax fee stamp
    bx0, by0, bx1, by1 = 556, 540, 958, 676
    cv.rect_outline(bx0, by0, bx1, by1, FEE_INK, width=2)
    cv.rect_outline(bx0 + 5, by0 + 5, bx1 - 5, by1 - 5, FEE_INK, width=1)
    # small anchor glyph
    ax, ay = bx0 + 34, by0 + 62
    cv.ellipse_outline(ax - 14, ay - 26, ax + 14, ay + 2, FEE_INK, width=3)
    cv.line(ax, ay - 34, ax, ay + 26, FEE_INK, width=3)
    cv.line(ax - 12, ay - 28, ax + 12, ay - 28, FEE_INK, width=3)
    cv.polyline([(ax - 16, ay + 14), (ax, ay + 30), (ax + 16, ay + 14)],
                FEE_INK, width=3)
    tx = bx0 + 62
    text(cv, tx, by0 + 16, "HARBOR TAX PAID", 15, FEE_INK)
    draw_text(cv, tx, by0 + 44, "40 SELENI  \u2014  VALID FOR ONE LANDING",
              FEE_INK, scale=1)
    text(cv, tx, by0 + 70, "PORT SELENE HARBOUR AUTHORITY", 10, FEE_INK)
    text(cv, tx, by0 + 90,
         "PAID 14 AUG 2025  \u00b7  RECEIPT No. HT-2025-0814", 10, FEE_INK)
    # handwritten-style note under the fee stamp
    text(cv, 556, 692, "Seaman's book endorsed \u2014 see p. 14.",
         11, (60, 60, 120))
    text(cv, 958, 716, "2", 11, INK_SOFT, anchor="ra")

    paper_noise(cv)
    png = encode_png(cv)
    outdir = os.path.dirname(OUT)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(png)
    print("wrote", OUT, (W, H), len(png), "bytes")


if __name__ == "__main__":
    build()
