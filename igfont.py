# -*- coding: utf-8 -*-
"""Bundled-font loader for cloud rendering (no macOS Hiragino needed).
Uses Noto Sans JP variable TTF (OFL) committed in assets/fonts/.
F(weight,size): weight 3..9 (Hiragino-style) -> Noto wght 300..900, cached."""
import os
from PIL import ImageFont

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts", "NotoSansJP.ttf")
_cache = {}

def F(weight, size):
    key = (int(weight), int(size))
    f = _cache.get(key)
    if f is None:
        f = ImageFont.truetype(FONT, int(size))
        try:
            f.set_variation_by_axes([min(900, max(100, int(weight) * 100))])
        except Exception:
            pass
        _cache[key] = f
    return f
