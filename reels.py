# -*- coding: utf-8 -*-
"""Naviris Reels generator — vertical 1080x1920 kinetic-typography MP4.
Renders frames with Pillow, encodes with ffmpeg. Data-driven beats."""
import os, math, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
BG_TOP = (13, 21, 42)
BG_BOT = (8, 12, 24)
INK = (240, 244, 252)
SUB = (150, 165, 190)
ACCENT = (60, 196, 255)
from igfont import F

def _bg():
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / H
        px_row = (int(BG_TOP[0]*(1-t)+BG_BOT[0]*t),
                  int(BG_TOP[1]*(1-t)+BG_BOT[1]*t),
                  int(BG_TOP[2]*(1-t)+BG_BOT[2]*t))
        for x in range(W):
            px[x, y] = px_row
    return img

# Pre-render a base background once (expensive), reuse per frame.
_BASE_BG = _bg()

def glow(img, cx, cy, rad, col, strength):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    steps = 22
    for i in range(steps, 0, -1):
        r = int(rad * i / steps)
        a = int(strength * (i / steps) * 0.05)
        gd.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(col[0], col[1], col[2], a))
    img.alpha_composite(g)

def wrap(draw, text, font, max_w):
    out, line = [], ""
    for ch in text:
        if ch == "\n":
            out.append(line); line = ""; continue
        if draw.textlength(line+ch, font=font) > max_w and line:
            out.append(line); line = ch
        else:
            line += ch
    out.append(line)
    return out

def ease_out(t):
    return 1 - (1 - t) ** 3

def render_frame(beat, local_t, beat_dur, gi, total_beats):
    img = _BASE_BG.copy().convert("RGBA")
    # moving glow
    gx = int(W*0.5 + math.sin(local_t*0.8 + gi)*180)
    gy = int(H*0.34 + math.cos(local_t*0.6 + gi)*120)
    glow(img, gx, gy, 760, ACCENT, beat.get("glow", 70))
    draw = ImageDraw.Draw(img)

    # entrance animation: fade + slide up over first 0.42s
    intro = min(1.0, local_t / 0.42)
    e = ease_out(intro)
    dy = int((1 - e) * 60)
    alpha = int(255 * e)

    size = beat.get("size", 104)
    hf = F(9, size)
    lines = wrap(draw, beat["text"], hf, W - 200)
    lh = size + 26
    block_h = lh * len(lines)
    y0 = H//2 - block_h//2 - 40 + dy

    # kicker
    if beat.get("kicker"):
        kf = F(7, 40)
        kw = draw.textlength(beat["kicker"], font=kf)
        layer = Image.new("RGBA", (W, H), (0,0,0,0))
        ld = ImageDraw.Draw(layer)
        ld.text(((W-kw)//2, y0-90+dy), beat["kicker"], font=kf, fill=ACCENT+(alpha,))
        img.alpha_composite(layer)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    col = beat.get("color", INK)
    y = y0
    for ln in lines:
        lw = ld.textlength(ln, font=hf)
        ld.text(((W-lw)//2, y), ln, font=hf, fill=col+(alpha,))
        y += lh
    # accent underline under block
    uw = 150
    ld.rounded_rectangle([(W-uw)//2, y+18, (W+uw)//2, y+30], 6, fill=ACCENT+(alpha,))
    img.alpha_composite(layer)

    draw = ImageDraw.Draw(img)
    # footer handle
    ff = F(5, 34)
    fw = draw.textlength("@naviris_inc", font=ff)
    draw.text(((W-fw)//2, H-150), "@naviris_inc", font=ff, fill=SUB)
    # progress segments
    seg_w = 60; gap = 14
    total_w = total_beats*seg_w + (total_beats-1)*gap
    x = (W-total_w)//2
    for i in range(total_beats):
        done = i < gi or (i == gi and local_t/beat_dur)
        fillc = ACCENT if i <= gi else (60, 74, 104)
        prog = 1.0 if i < gi else (local_t/beat_dur if i == gi else 0.0)
        draw.rounded_rectangle([x, H-90, x+seg_w, H-84], 3, fill=(60,74,104))
        draw.rounded_rectangle([x, H-90, x+int(seg_w*prog), H-84], 3, fill=ACCENT)
        x += seg_w+gap
    return img.convert("RGB")

def build_reel(beats, out_path, audio=None):
    tmp = out_path + "_frames"
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    fidx = 0
    for gi, beat in enumerate(beats):
        dur = beat["dur"]
        n = int(dur * FPS)
        for f in range(n):
            lt = f / FPS
            frame = render_frame(beat, lt, dur, gi, len(beats))
            frame.save(os.path.join(tmp, f"f_{fidx:05d}.png"))
            fidx += 1
    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "f_%05d.png")]
    if audio:
        cmd += ["-i", audio, "-shortest", "-c:a", "aac", "-b:a", "128k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-vf", "scale=1080:1920", out_path]
    subprocess.run(cmd, check=True, capture_output=True)
    shutil.rmtree(tmp)
    return out_path

if __name__ == "__main__":
    beats = [
        {"kicker": "NAVIRIS", "text": "「とりあえず大手」で、\nほんとにいい？", "size": 92, "dur": 2.0},
        {"text": "学歴より、年齢より、", "size": 96, "dur": 1.6},
        {"text": "20代で“営業力”を\n持ってる奴が強い。", "size": 92, "dur": 2.2},
        {"text": "断られて、また行く。", "size": 100, "dur": 1.6},
        {"text": "その回数だけ、\n人は強くなる。", "size": 96, "dur": 2.2},
        {"kicker": "RECRUIT", "text": "関東・光回線の\n営業インターン", "size": 92, "dur": 2.0},
        {"text": "学歴/年齢/大学生\n不問・歩合", "size": 92, "color": ACCENT, "dur": 2.0},
        {"kicker": "ENTRY", "text": "プロフのLINEから\n話を聞きにこい", "size": 90, "dur": 2.4},
    ]
    out = os.path.join(os.path.dirname(__file__), "posts", "reel01.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build_reel(beats, out)
    print("OK", out)
