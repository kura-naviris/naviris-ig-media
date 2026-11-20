# -*- coding: utf-8 -*-
"""Naviris online-meeting background renderer (1920x1080).

Reuses the IG carousel brand system (deep navy, cyan accent, Noto Sans JP)
so Zoom/Meet/Teams backgrounds match the @naviris_inc feed.
Outputs PNGs to assets/meeting_bg/.
"""
import math
import os

from PIL import Image, ImageDraw

from igfont import F

W, H = 1920, 1080
BG_TOP = (12, 20, 40)
BG_BOT = (8, 12, 26)
INK = (240, 244, 252)
SUB = (150, 165, 190)
ACCENT = (60, 196, 255)
ACCENT2 = (46, 123, 255)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "meeting_bg")


def gradient(img):
    px = img.load()
    for yy in range(H):
        t = yy / H
        r = int(BG_TOP[0] * (1 - t) + BG_BOT[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOT[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOT[2] * t)
        for xx in range(W):
            px[xx, yy] = (r, g, b, 255)


def glow(img, cx, cy, rad, col, strength=60):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for i in range(rad, 0, -8):
        a = int(strength * (i / rad) * 0.06)
        gd.ellipse([cx - i, cy - i, cx + i, cy + i], fill=(col[0], col[1], col[2], a))
    img.alpha_composite(g)


def ring(img, cx, cy, rad, col, alpha, width=2):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse([cx - rad, cy - rad, cx + rad, cy + rad],
               outline=(col[0], col[1], col[2], alpha), width=width)
    img.alpha_composite(g)


def logo_mark(img, x, y, s, col=ACCENT):
    """Compass-needle mark: two chevrons pointing up-right, brand cyan/blue."""
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    # split compass needle pointing up-right (paper-plane fold)
    a = (x, y + s)                       # bottom-left
    b = (x + s * 0.74, y)                # tip
    c = (x + s * 0.46, y + s * 0.70)     # inner fold
    d = (x + s * 0.62, y + s)            # bottom-right
    gd.polygon([a, b, c], fill=col + (255,))
    gd.polygon([c, b, d], fill=ACCENT2 + (255,))
    img.alpha_composite(g)


def wordmark(img, x, y, size, with_mark=True, sub=None):
    draw = ImageDraw.Draw(img)
    f = F(8, size)
    mx = x
    if with_mark:
        s = size * 0.92
        logo_mark(img, x, y + size * 0.14, s)
        draw = ImageDraw.Draw(img)
        mx = x + s * 0.62 + size * 0.34
    draw.text((mx, y), "NAVIRIS", font=f, fill=INK)
    b = draw.textbbox((mx, y), "NAVIRIS", font=f)
    # cyan dot after the wordmark
    r = max(3, size // 11)
    draw.ellipse([b[2] + r * 2, b[3] - r * 2, b[2] + r * 4, b[3]], fill=ACCENT)
    if sub:
        sf = F(5, int(size * 0.30))
        draw.text((mx + 2, b[3] + size * 0.22), sub, font=sf, fill=SUB)
    return b


def base():
    img = Image.new("RGBA", (W, H), BG_BOT + (255,))
    gradient(img)
    glow(img, 1700, 140, 560, ACCENT, 80)
    glow(img, 200, 1000, 640, ACCENT2, 70)
    ring(img, 1700, 140, 330, ACCENT, 34)
    ring(img, 1700, 140, 430, ACCENT, 18)
    ring(img, 200, 1000, 380, ACCENT2, 26)
    return img


def bottom_bar(img):
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, H - 10, W, H], fill=ACCENT2)
    draw.rectangle([0, H - 10, int(W * 0.34), H], fill=ACCENT)


def variant_corner(path):
    """Logo top-left, handle bottom-right. Face stays clear in the center."""
    img = base()
    wordmark(img, 72, 56, 64, sub="株式会社Naviris")
    draw = ImageDraw.Draw(img)
    f = F(5, 30)
    t = "@naviris_inc"
    b = draw.textbbox((0, 0), t, font=f)
    draw.text((W - 72 - (b[2] - b[0]), H - 64 - (b[3] - b[1])), t, font=f, fill=SUB)
    bottom_bar(img)
    img.convert("RGB").save(path, "PNG")


def variant_center(path):
    """Big centered wordmark high on the frame — for title/waiting screens."""
    img = base()
    draw = ImageDraw.Draw(img)
    f = F(9, 150)
    t = "NAVIRIS"
    b = draw.textbbox((0, 0), t, font=f)
    tw = b[2] - b[0]
    s = 140
    total = s * 0.62 + 50 + tw
    x0 = (W - total) / 2
    logo_mark(img, x0, 150 + 20, s)
    draw = ImageDraw.Draw(img)
    draw.text((x0 + s * 0.62 + 50, 150), t, font=f, fill=INK)
    sf = F(5, 40)
    st = "株式会社Naviris"
    sb = draw.textbbox((0, 0), st, font=sf)
    draw.text(((W - (sb[2] - sb[0])) / 2, 360), st, font=sf, fill=SUB)
    bottom_bar(img)
    img.convert("RGB").save(path, "PNG")


def variant_minimal(path):
    """Quietest option: small mark only, bottom-left, for busy calls."""
    img = Image.new("RGBA", (W, H), BG_BOT + (255,))
    gradient(img)
    glow(img, 1760, 1000, 520, ACCENT2, 55)
    ring(img, 1760, 1000, 300, ACCENT, 22)
    wordmark(img, 72, H - 150, 44)
    bottom_bar(img)
    img.convert("RGB").save(path, "PNG")


def main():
    os.makedirs(OUT, exist_ok=True)
    variant_corner(os.path.join(OUT, "naviris_meeting_bg_corner.png"))
    variant_center(os.path.join(OUT, "naviris_meeting_bg_center.png"))
    variant_minimal(os.path.join(OUT, "naviris_meeting_bg_minimal.png"))
    print("done ->", OUT)


if __name__ == "__main__":
    main()
