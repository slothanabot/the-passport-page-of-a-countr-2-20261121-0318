#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws an open passport spread for the island Sultanate of Kalypsis
(capital Port Selene): a data page with a drawn portrait and an MRZ strip,
and a facing page of arrival/departure stamps from the neighbouring
countries Thessaly and Corvina, plus a harbour-tax fee stamp.

Pure local drawing with Pillow. Deterministic: fixed seed, no randomness
in layout, no network, no external images. Fonts are shipped in fonts/.
Writes one PNG to /output/entry.png (or $OUTPUT_PATH).
"""
import os
import random

from PIL import Image, ImageDraw, ImageFont

S = 2  # supersample factor; final image is W x H
W, H = 1024, 768
OUT = os.environ.get("OUTPUT_PATH", "/output/entry.png")
BASE = os.path.dirname(os.path.abspath(__file__))

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


def font(name, size):
    return ImageFont.truetype(os.path.join(BASE, "fonts", name), int(size * S))


F_SERIF = lambda sz: font("DejaVuSerif.ttf", sz)
F_SERIF_B = lambda sz: font("DejaVuSerif-Bold.ttf", sz)
F_SANS_B = lambda sz: font("DejaVuSans-Bold.ttf", sz)
F_MONO = lambda sz: font("DejaVuSansMono.ttf", sz)


def sc(v):
    return int(round(v * S))


# ---------------------------------------------------------------- helpers
def text(draw, x, y, s, f, fill=INK, anchor="la"):
    draw.text((sc(x), sc(y)), s, font=f, fill=fill, anchor=anchor)


def hline(draw, x0, x1, y, fill=RULE, width=1):
    draw.line([(sc(x0), sc(y)), (sc(x1), sc(y))], fill=fill, width=sc(width))


def rect(draw, x0, y0, x1, y1, outline=None, width=1, fill=None):
    draw.rectangle([sc(x0), sc(y0), sc(x1), sc(y1)],
                   outline=outline, width=sc(width), fill=fill)


def paper_noise(img, seed=42):
    """Deterministic faint ageing: speckles and a soft vignette."""
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    for _ in range(2600):
        x = rng.randrange(w)
        y = rng.randrange(h)
        v = rng.randrange(-14, 10)
        r, g, b = px[x, y]
        px[x, y] = (max(0, min(255, r + v)),
                    max(0, min(255, g + v)),
                    max(0, min(255, b + v)))
    # vignette: darken edges slightly
    ov = Image.new("L", (w, h), 0)
    od = ImageDraw.Draw(ov)
    od.rectangle([0, 0, w - 1, h - 1], outline=26, width=90)
    dark = Image.new("RGB", (w, h), (120, 100, 60))
    img.paste(dark, (0, 0), ov.point(lambda p: p // 4))


def mrz_check(s):
    vals = {}
    for i in range(10):
        vals[str(i)] = i
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
def draw_portrait(base, x0, y0, x1, y1):
    """Stylised dignified bust of Mara Eleni Selene, drawn with shapes."""
    pw, ph = sc(x1 - x0), sc(y1 - y0)
    layer = Image.new("RGB", (pw, ph), (96, 138, 130))
    d = ImageDraw.Draw(layer)
    # backdrop: soft vertical gradient + faint arch
    for i in range(ph):
        t = i / ph
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((126, 168, 158), (62, 104, 96)))
        d.line([(0, i), (pw, i)], fill=c)
    # (no halo/arch outline: keep the backdrop plain behind the head)
    cx = pw * 0.50
    # shoulders / garment: deep teal robe with gold collar
    d.polygon([(pw * 0.10, ph), (pw * 0.30, ph * 0.74),
               (pw * 0.70, ph * 0.74), (pw * 0.90, ph)],
              fill=(16, 74, 76))
    d.polygon([(pw * 0.38, ph * 0.78), (pw * 0.50, ph * 0.86),
               (pw * 0.62, ph * 0.78), (pw * 0.50, ph * 0.72)],
              fill=GOLD)
    # small crescent brooch
    d.ellipse([pw * 0.46, ph * 0.88, pw * 0.54, ph * 0.96], fill=GOLD)
    d.ellipse([pw * 0.475, ph * 0.885, pw * 0.54, ph * 0.955],
              fill=(16, 74, 76))
    # neck
    d.rectangle([cx - pw * 0.055, ph * 0.62, cx + pw * 0.055, ph * 0.76],
                fill=SKIN_DARK)
    # head
    d.ellipse([cx - pw * 0.155, ph * 0.10, cx + pw * 0.155, ph * 0.62],
              fill=SKIN)
    # ears
    d.ellipse([cx - pw * 0.185, ph * 0.33, cx - pw * 0.13, ph * 0.45],
              fill=SKIN)
    d.ellipse([cx + pw * 0.13, ph * 0.33, cx + pw * 0.185, ph * 0.45],
              fill=SKIN)
    # hair: dark mass over the crown, parted centre, bun at the back
    d.pieslice([cx - pw * 0.175, ph * 0.02, cx + pw * 0.175, ph * 0.52],
               180, 360, fill=HAIR)
    d.ellipse([cx - pw * 0.175, ph * 0.06, cx - pw * 0.06, ph * 0.34],
              fill=HAIR)
    d.ellipse([cx + pw * 0.06, ph * 0.06, cx + pw * 0.175, ph * 0.34],
              fill=HAIR)
    d.ellipse([cx + pw * 0.10, ph * 0.02, cx + pw * 0.22, ph * 0.20],
              fill=HAIR)  # bun
    d.arc([cx + pw * 0.10, ph * 0.02, cx + pw * 0.22, ph * 0.20],
          0, 360, fill=(30, 20, 12), width=sc(2))
    # brows, eyes, nose, lips — simple, calm, front-facing
    d.line([(cx - pw * 0.105, ph * 0.335), (cx - pw * 0.035, ph * 0.325)],
           fill=HAIR, width=sc(2))
    d.line([(cx + pw * 0.035, ph * 0.325), (cx + pw * 0.105, ph * 0.335)],
           fill=HAIR, width=sc(2))
    d.ellipse([cx - pw * 0.095, ph * 0.345, cx - pw * 0.045, ph * 0.375],
              fill=(40, 28, 20))
    d.ellipse([cx + pw * 0.045, ph * 0.345, cx + pw * 0.095, ph * 0.375],
              fill=(40, 28, 20))
    d.line([(cx, ph * 0.38), (cx - pw * 0.008, ph * 0.47)],
           fill=SKIN_DARK, width=sc(2))
    d.line([(cx - pw * 0.045, ph * 0.505), (cx + pw * 0.045, ph * 0.505)],
           fill=(150, 80, 70), width=sc(3))
    # cheek shading
    d.ellipse([cx - pw * 0.13, ph * 0.42, cx - pw * 0.06, ph * 0.48],
              fill=(226, 168, 128))
    d.ellipse([cx + pw * 0.06, ph * 0.42, cx + pw * 0.13, ph * 0.48],
              fill=(226, 168, 128))
    base.paste(layer, (sc(x0), sc(y0)))


def draw_arms(draw, cx, cy, r):
    """Coat of arms: gold disc, crescent moon, star, three waves."""
    draw.ellipse([sc(cx - r), sc(cy - r), sc(cx + r), sc(cy + r)],
                 outline=GOLD, width=sc(2))
    draw.ellipse([sc(cx - r * 0.55), sc(cy - r * 0.55),
                  sc(cx + r * 0.55), sc(cy + r * 0.55)], fill=GOLD)
    draw.ellipse([sc(cx - r * 0.28), sc(cy - r * 0.55),
                  sc(cx + r * 0.72), sc(cy + r * 0.45)], fill=PAPER)
    # star
    sx, sy = cx + r * 0.28, cy - r * 0.28
    draw.polygon([(sc(sx), sc(sy - 7)), (sc(sx + 2), sc(sy - 2)),
                  (sc(sx + 7), sc(sy)), (sc(sx + 2), sc(sy + 2)),
                  (sc(sx), sc(sy + 7)), (sc(sx - 2), sc(sy + 2)),
                  (sc(sx - 7), sc(sy)), (sc(sx - 2), sc(sy - 2))],
                 fill=GOLD)
    # waves
    for i, wy in enumerate((cy + r * 0.62, cy + r * 0.74)):
        draw.arc([sc(cx - r * 0.8), sc(wy - 5), sc(cx + r * 0.8), sc(wy + 5)],
                 180, 360, fill=TEAL, width=sc(2))


# ---------------------------------------------------------------- stamps
def make_stamp(kind, lines, ink, angle, w, h):
    """Return an RGBA stamp layer (final-size coords) to paste rotated."""
    layer = Image.new("RGBA", (sc(w), sc(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = sc(w) / 2, sc(h) / 2
    lw = sc(3)
    if kind == "circle":
        d.ellipse([lw, lw, sc(w) - lw, sc(h) - lw], outline=ink + (230,),
                  width=lw)
        d.ellipse([sc(7), sc(7), sc(w - 7), sc(h - 7)], outline=ink + (230,),
                  width=sc(2))
    elif kind == "oval":
        d.ellipse([lw, lw, sc(w) - lw, sc(h) - lw], outline=ink + (230,),
                  width=lw)
        d.ellipse([sc(6), sc(6), sc(w - 6), sc(h - 6)], outline=ink + (230,),
                  width=sc(2))
    else:  # rectangle
        d.rectangle([lw, lw, sc(w) - lw, sc(h) - lw], outline=ink + (230,),
                    width=lw)
        d.rectangle([sc(6), sc(6), sc(w - 6), sc(h - 6)],
                    outline=ink + (230,), width=sc(2))
    # text lines, centred
    n = len(lines)
    for i, (s, f, col) in enumerate(lines):
        y = sc(h) / 2 + (i - (n - 1) / 2) * sc(13) - sc(6)
        d.text((cx, y), s, font=f, fill=col + (235,), anchor="ma")
    return layer.rotate(angle, expand=False, resample=Image.BICUBIC)


def paste_stamp(img, layer, x, y):
    img.paste(layer, (sc(x), sc(y)), layer)


# ---------------------------------------------------------------- build
def build():
    img = Image.new("RGB", (sc(W), sc(H)), DESK)
    d = ImageDraw.Draw(img, "RGBA")

    # ---- spread: two paper pages with a gutter
    x0, y0, x1, y1 = 36, 28, 988, 740
    mid = (x0 + x1) / 2
    d.rectangle([sc(x0), sc(y0), sc(x1), sc(y1)], fill=PAPER)
    d.rectangle([sc(x0), sc(y0), sc(x1), sc(y0 + 4)], fill=PAPER_DARK)
    d.rectangle([sc(x0), sc(y1 - 4), sc(x1), sc(y1)], fill=PAPER_DARK)
    # gutter shadow
    for i in range(14):
        a = 46 - i * 3
        d.line([(sc(mid - 7 + i), sc(y0)), (sc(mid - 7 + i), sc(y1))],
               fill=(90, 70, 40, max(a, 0)), width=sc(1))
    d.line([(sc(mid), sc(y0)), (sc(mid), sc(y1))], fill=(150, 125, 85),
           width=sc(1))
    # perforated passport number along the top edge of the spread
    for i in range(46):
        px = x0 + 14 + i * 20
        d.text((sc(px), sc(y0 + 8)), "KLY048177", font=F_MONO(7),
               fill=(140, 115, 75), anchor="la")

    # faint watermark on both pages
    wm = Image.new("RGBA", img.size, (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    wd.text((sc(274), sc(430)), "KALYPSIS", font=F_SERIF_B(64),
            fill=(150, 120, 60, 26), anchor="mm")
    wd.text((sc(750), sc(430)), "KALYPSIS", font=F_SERIF_B(64),
            fill=(150, 120, 60, 26), anchor="mm")
    wm = wm.rotate(-24, center=(sc(512), sc(384)), resample=Image.BICUBIC)
    img.paste(wm, (0, 0), wm)
    d = ImageDraw.Draw(img, "RGBA")

    # ================================================= LEFT PAGE: data page
    cxL = 274
    draw_arms(d, 96, 66, 16)
    text(d, cxL, 46, "SULTANATE OF KALYPSIS", F_SERIF_B(19), anchor="ma")
    text(d, cxL, 72, "PASSPORT  ·  PASSEPORT", F_SERIF(12), INK_SOFT,
         anchor="ma")
    hline(d, 66, 482, 94, width=1)
    hline(d, 66, 482, 97, width=1)

    # portrait
    rect(d, 66, 116, 206, 296, outline=INK, width=1)
    rect(d, 70, 120, 202, 292, outline=RULE, width=1)
    draw_portrait(img, 71, 121, 201, 291)
    d = ImageDraw.Draw(img, "RGBA")
    text(d, 136, 300, "PHOTOGRAPH OF HOLDER", F_SANS_B(7), INK_SOFT,
         anchor="ma")

    # data fields, right of the portrait
    fx, fw = 224, 268
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
        text(d, fx, y, label, F_SANS_B(8), INK_SOFT)
        if row[2] is None:
            text(d, fx, y + 11, value, F_SERIF_B(13))
            y += 30
        else:
            # first row: three short fields side by side
            text(d, fx, y + 11, value, F_SERIF_B(13))
            text(d, fx + 62, y, row[2], F_SANS_B(8), INK_SOFT)
            text(d, fx + 62, y + 11, row[3], F_SERIF_B(13))
            text(d, fx + 128, y, row[4], F_SANS_B(8), INK_SOFT)
            text(d, fx + 128, y + 11, row[5], F_SERIF_B(13))
            y += 30
    # signature
    sy = y + 4
    text(d, fx, sy, "HOLDER'S SIGNATURE", F_SANS_B(8), INK_SOFT)
    d.line([(sc(fx), sc(sy + 26)), (sc(fx + 200), sc(sy + 26))],
           fill=INK, width=sc(1))
    sig = Image.new("RGBA", (sc(220), sc(26)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sig)
    sd.line([(sc(6), sc(18)), (sc(40), sc(6)), (sc(70), sc(20)),
             (sc(100), sc(8)), (sc(130), sc(19)), (sc(160), sc(10)),
             (sc(190), sc(17))], fill=(30, 40, 90, 235), width=sc(2))
    sig = sig.rotate(-4, resample=Image.BICUBIC)
    img.paste(sig, (sc(fx), sc(sy + 8)), sig)
    d = ImageDraw.Draw(img, "RGBA")

    # MRZ strip
    mrz_y = 640
    rect(d, 56, mrz_y - 12, 492, mrz_y + 46, fill=(238, 228, 200))
    hline(d, 56, 492, mrz_y - 12, fill=INK, width=1)
    l1, l2 = mrz_lines()
    text(d, 66, mrz_y - 4, l1, F_MONO(13))
    text(d, 66, mrz_y + 16, l2, F_MONO(13))
    text(d, 482, 716, "1", F_SERIF(11), INK_SOFT, anchor="ra")

    # ================================================= RIGHT PAGE: visas
    cxR = 750
    text(d, cxR, 46, "VISAS", F_SERIF_B(19), anchor="ma")
    text(d, cxR, 72, "VISA  ·  ENTRY AND EXIT STAMPS", F_SERIF(11),
         INK_SOFT, anchor="ma")
    hline(d, 542, 958, 94, width=1)
    hline(d, 542, 958, 97, width=1)

    stamps = [
        # (kind, x, y, w, h, angle, ink, lines)
        ("oval", 556, 116, 190, 74, -7, STAMP_BLUE, [
            ("THESSALY", F_SANS_B(11), STAMP_BLUE),
            ("ARRIVAL  ·  12 SEP 2023", F_SANS_B(9), STAMP_BLUE),
            ("PORT OF VOLOS", F_SANS_B(8), STAMP_BLUE)]),
        ("rect", 772, 122, 170, 62, 5, STAMP_BLUE, [
            ("THESSALY — DEPARTURE", F_SANS_B(9), STAMP_BLUE),
            ("26 SEP 2023 · VOLOS", F_SANS_B(9), STAMP_BLUE)]),
        ("circle", 556, 224, 120, 120, 9, STAMP_RED, [
            ("CORVINA", F_SANS_B(11), STAMP_RED),
            ("ARRIVAL", F_SANS_B(10), STAMP_RED),
            ("08 FEB 2024", F_SANS_B(10), STAMP_RED),
            ("· RIVA ·", F_SANS_B(8), STAMP_RED)]),
        ("rect", 716, 252, 210, 62, -5, STAMP_RED, [
            ("CORVINA — DEPARTURE", F_SANS_B(9), STAMP_RED),
            ("19 FEB 2024 · RIVA HARBOUR", F_SANS_B(8), STAMP_RED)]),
        ("oval", 556, 372, 190, 74, 6, STAMP_PURPLE, [
            ("THESSALY", F_SANS_B(11), STAMP_PURPLE),
            ("ARRIVAL  ·  03 MAY 2025", F_SANS_B(9), STAMP_PURPLE),
            ("PORT OF VOLOS", F_SANS_B(8), STAMP_PURPLE)]),
        ("circle", 786, 372, 120, 120, -9, STAMP_PURPLE, [
            ("CORVINA", F_SANS_B(11), STAMP_PURPLE),
            ("ARRIVAL", F_SANS_B(10), STAMP_PURPLE),
            ("14 AUG 2025", F_SANS_B(10), STAMP_PURPLE),
            ("· RIVA ·", F_SANS_B(8), STAMP_PURPLE)]),
    ]
    for kind, x, y, w, h, ang, ink, lines in stamps:
        layer = make_stamp(kind, lines, ink, ang, w, h)
        paste_stamp(img, layer, x, y)
    d = ImageDraw.Draw(img, "RGBA")

    # ---- the telling paperwork detail: harbour-tax fee stamp
    bx0, by0, bx1, by1 = 556, 540, 958, 676
    rect(d, bx0, by0, bx1, by1, outline=FEE_INK, width=2)
    rect(d, bx0 + 5, by0 + 5, bx1 - 5, by1 - 5, outline=FEE_INK, width=1)
    # small anchor glyph
    ax, ay = bx0 + 34, by0 + 62
    d.ellipse([sc(ax - 14), sc(ay - 26), sc(ax + 14), sc(ay + 2)],
              outline=FEE_INK, width=sc(3))
    d.line([(sc(ax), sc(ay - 34)), (sc(ax), sc(ay + 26))], fill=FEE_INK,
           width=sc(3))
    d.line([(sc(ax - 12), sc(ay - 28)), (sc(ax + 12), sc(ay - 28))],
           fill=FEE_INK, width=sc(3))
    d.line([(sc(ax - 16), sc(ay + 14)), (sc(ax), sc(ay + 30)),
            (sc(ax + 16), sc(ay + 14))], fill=FEE_INK, width=sc(3))
    tx = bx0 + 62
    text(d, tx, by0 + 16, "HARBOR TAX PAID", F_SANS_B(15), FEE_INK)
    text(d, tx, by0 + 44, "40 SELENI  —  VALID FOR ONE LANDING",
         F_SANS_B(12), FEE_INK)
    text(d, tx, by0 + 70, "PORT SELENE HARBOUR AUTHORITY", F_SANS_B(10),
         FEE_INK)
    text(d, tx, by0 + 90, "PAID 14 AUG 2025  ·  RECEIPT No. HT-2025-0814",
         F_SANS_B(10), FEE_INK)
    # handwritten-style note under the fee stamp
    text(d, 556, 692, "Seaman's book endorsed — see p. 14.",
         F_SERIF(11), (60, 60, 120))
    text(d, 958, 716, "2", F_SERIF(11), INK_SOFT, anchor="ra")

    paper_noise(img)
    img = img.resize((W, H), Image.LANCZOS)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print("wrote", OUT, img.size)


if __name__ == "__main__":
    build()
