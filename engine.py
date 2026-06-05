# -*- coding: utf-8 -*-
"""Naviris IG carousel engine. Data-driven slide renderer (1080x1350)."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1350
MARGIN = 96
BG = (10, 16, 32)          # deep navy
BG2 = (14, 22, 44)         # panel navy
INK = (240, 244, 252)      # near-white
SUB = (150, 165, 190)      # muted
ACCENT = (60, 196, 255)    # cyan-blue "light"
ACCENT2 = (46, 123, 255)   # blue
GOLD = (255, 209, 102)     # number/emphasis warm

from igfont import F

def measure(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2]-b[0], b[3]-b[1]

def wrap(draw, text, font, max_w):
    """Char-based wrapping for Japanese; respects explicit \n."""
    out = []
    for para in text.split("\n"):
        if para == "":
            out.append("")
            continue
        line = ""
        for ch in para:
            test = line + ch
            w, _ = measure(draw, test, font)
            if w > max_w and line:
                out.append(line)
                line = ch
            else:
                line = test
        out.append(line)
    return out

def draw_lines(draw, lines, font, x, y, lh, color):
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=color)
        y += lh
    return y

def gradient_bg(img):
    """Subtle vertical gradient + corner glow."""
    top = (12, 20, 40); bot = (8, 12, 26)
    px = img.load()
    for yy in range(H):
        t = yy / H
        r = int(top[0]*(1-t)+bot[0]*t)
        g = int(top[1]*(1-t)+bot[1]*t)
        b = int(top[2]*(1-t)+bot[2]*t)
        for xx in range(W):
            px[xx, yy] = (r, g, b)

def glow(img, cx, cy, rad, col, strength=60):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for i in range(rad, 0, -8):
        a = int(strength * (i/rad) * 0.06)
        gd.ellipse([cx-i, cy-i, cx+i, cy+i], fill=(col[0], col[1], col[2], a))
    img.alpha_composite(g)

def dots(draw, idx, total, y):
    n = total
    gap = 26; r = 5
    tw = (n-1)*gap
    x0 = W//2 - tw//2
    for i in range(n):
        cx = x0 + i*gap
        col = ACCENT if i == idx else (70, 84, 110)
        draw.ellipse([cx-r, cy_(cx, y, r)[1]-r, cx+r, cy_(cx, y, r)[1]+r], fill=col)

def cy_(cx, y, r):
    return (cx, y)

def footer(draw, idx, total):
    f = F(5, 30)
    draw.text((MARGIN, H-78), "@naviris_inc", font=f, fill=SUB)
    fn = F(6, 30)
    label = f"{idx+1:02d} / {total:02d}"
    w, _ = measure(draw, label, fn)
    draw.text((W-MARGIN-w, H-78), label, font=fn, fill=SUB)

def render_slide(slide, idx, total, path):
    img = Image.new("RGBA", (W, H), BG+(255,))
    gradient_bg_rgba(img)
    draw = ImageDraw.Draw(img)
    kind = slide.get("kind", "content")

    if kind == "cover":
        glow(img, 880, 230, 520, ACCENT, 90)
        draw = ImageDraw.Draw(img)
        # kicker
        k = F(7, 34)
        draw.text((MARGIN, 150), slide.get("kicker", "NAVIRIS"), font=k, fill=ACCENT)
        # headline
        hf = F(9, slide.get("size", 104))
        lines = wrap(draw, slide["title"], hf, W-2*MARGIN)
        y = 300
        lh = slide.get("size", 104) + 26
        for ln in lines:
            draw.text((MARGIN, y), ln, font=hf, fill=INK)
            y += lh
        # accent underline
        draw.rounded_rectangle([MARGIN, y+10, MARGIN+150, y+24], 7, fill=ACCENT)
        # sub
        if slide.get("sub"):
            sf = F(4, 40)
            sl = wrap(draw, slide["sub"], sf, W-2*MARGIN)
            draw_lines(draw, sl, sf, MARGIN, y+70, 60, SUB)
        # swipe hint
        sw = F(6, 32)
        draw.text((MARGIN, H-150), "← スワイプ", font=sw, fill=ACCENT)

    elif kind == "cta":
        glow(img, 540, 1150, 620, ACCENT2, 90)
        draw = ImageDraw.Draw(img)
        k = F(7, 34)
        draw.text((MARGIN, 170), slide.get("kicker", "ENTRY"), font=k, fill=ACCENT)
        hf = F(9, slide.get("size", 88))
        lines = wrap(draw, slide["title"], hf, W-2*MARGIN)
        y = 300
        lh = slide.get("size", 88) + 24
        for ln in lines:
            draw.text((MARGIN, y), ln, font=hf, fill=INK)
            y += lh
        if slide.get("sub"):
            sf = F(4, 40)
            sl = wrap(draw, slide["sub"], sf, W-2*MARGIN)
            y = draw_lines(draw, sl, sf, MARGIN, y+50, 62, SUB)
        # LINE button pill
        bf = F(8, 46)
        label = slide.get("button", "プロフのリンク → LINEで応募")
        bw, bh = measure(draw, label, bf)
        bx0, by0 = MARGIN, H-300
        draw.rounded_rectangle([bx0, by0, bx0+bw+96, by0+bh+56], 40, fill=ACCENT)
        draw.text((bx0+48, by0+22), label, font=bf, fill=(8, 14, 28))

    else:  # content
        # number badge
        nb = F(9, 132)
        num = slide.get("no", f"{idx:02d}")
        draw.text((MARGIN, 150), num, font=nb, fill=ACCENT)
        # headline
        hf = F(8, slide.get("size", 66))
        hlines = wrap(draw, slide["title"], hf, W-2*MARGIN)
        y = 330
        lh = slide.get("size", 66) + 18
        for ln in hlines:
            draw.text((MARGIN, y), ln, font=hf, fill=INK)
            y += lh
        # divider
        y += 14
        draw.line([MARGIN, y, W-MARGIN, y], fill=(40, 54, 84), width=3)
        y += 50
        # body
        if slide.get("body"):
            bf = F(3, 44)
            blines = wrap(draw, slide["body"], bf, W-2*MARGIN)
            draw_lines(draw, blines, bf, MARGIN, y, 72, (205, 214, 230))

    d2 = ImageDraw.Draw(img)
    footer(d2, idx, total)
    img.convert("RGB").save(path, "PNG")

def gradient_bg_rgba(img):
    top = (13, 21, 42); bot = (8, 12, 24)
    base = Image.new("RGB", (W, H))
    px = base.load()
    for yy in range(H):
        t = yy / H
        r = int(top[0]*(1-t)+bot[0]*t)
        g = int(top[1]*(1-t)+bot[1]*t)
        b = int(top[2]*(1-t)+bot[2]*t)
        for xx in range(W):
            px[xx, yy] = (r, g, b)
    img.paste(base, (0, 0))

def build(slides, outdir, prefix):
    os.makedirs(outdir, exist_ok=True)
    total = len(slides)
    paths = []
    for i, s in enumerate(slides):
        p = os.path.join(outdir, f"{prefix}_{i+1:02d}.png")
        render_slide(s, i, total, p)
        paths.append(p)
    return paths
