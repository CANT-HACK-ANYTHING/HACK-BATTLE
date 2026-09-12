"""Read amount / labels off the glass. Pixels only.

Python standard library + Pillow. No Tesseract binary, no Ollama, no
network. Templates are painted with the same DejaVu faces Ledger2005 uses.
"""

from __future__ import annotations

import functools
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

import config

_AMOUNT_RE = re.compile(
    r"(?:rs\.?|inr|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})+|[0-9]+)",
    re.IGNORECASE,
)

_FONT_REG = config.FONT_REG
_FONT_BOLD = config.FONT_BOLD

# Ledger2005 paint sizes
_AMT_SIZE = 26
_UI_SIZE = 15
_TITLE_SIZE = 16


def load_glass(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def crop_box(img: Image.Image, box: tuple[int, int, int, int] | list[int]) -> Image.Image:
    x, y, w, h = [int(v) for v in box]
    x = max(0, x)
    y = max(0, y)
    return img.crop((x, y, min(img.width, x + w), min(img.height, y + h)))


def _font(path: str, size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _glyph(ch: str, size: int, bold: bool, fill: int = 0, bg: int = 255) -> Image.Image:
    font = _font(_FONT_BOLD if bold else _FONT_REG, size)
    dummy = Image.new("L", (8, 8), bg)
    dr = ImageDraw.Draw(dummy)
    x0, y0, x1, y1 = dr.textbbox((0, 0), ch, font=font)
    w = max(1, x1 - x0 + 2)
    h = max(1, y1 - y0 + 2)
    im = Image.new("L", (w, h), bg)
    ImageDraw.Draw(im).text((1 - x0, 1 - y0), ch, font=font, fill=fill)
    return im


def _binarize(img: Image.Image) -> Image.Image:
    """Ink=0, paper=255. Inverts light-on-dark (Submit button)."""
    g = ImageOps.grayscale(img)
    if g.width < 2 or g.height < 2:
        return g.point(lambda p: 255)
    hist = g.histogram()
    # background = most common luminance
    bg = max(range(256), key=lambda i: hist[i])
    if bg < 110:
        g = ImageOps.invert(g)
        bg = 255 - bg
    cut = max(40, bg - 48)
    return g.point(lambda p: 0 if p < cut else 255)


def _ink_bbox(mask: Image.Image) -> tuple[int, int, int, int] | None:
    px = mask.load()
    w, h = mask.size
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if px[x, y] < 128:
                if x < minx:
                    minx = x
                if y < miny:
                    miny = y
                if x > maxx:
                    maxx = x
                if y > maxy:
                    maxy = y
    if maxx < minx:
        return None
    return minx, miny, maxx - minx + 1, maxy - miny + 1


def _score(mask: Image.Image, tmpl: Image.Image, x: int, y: int) -> float:
    """Fraction of template ink that lands on crop ink. Penalize empty paper."""
    tw, th = tmpl.size
    if x < 0 or y < 0 or x + tw > mask.width or y + th > mask.height:
        return 0.0
    crop = mask.crop((x, y, x + tw, y + th))
    a = crop.tobytes()
    b = tmpl.tobytes()
    n = len(b)
    if n == 0:
        return 0.0
    ink = 0
    hit = 0
    false = 0
    for i in range(n):
        tb = b[i] < 128
        cb = a[i] < 128
        if tb:
            ink += 1
            if cb:
                hit += 1
        elif cb:
            false += 1
    if ink == 0:
        return 0.0
    return (hit / ink) - 0.25 * (false / n)


@functools.lru_cache(maxsize=8)
def _digit_bank(size: int, bold: bool) -> list[tuple[str, Image.Image]]:
    bank = []
    for ch in "0123456789,":
        raw = _glyph(ch, size, bold)
        mask = _binarize(raw)
        box = _ink_bbox(mask)
        if box:
            x, y, w, h = box
            mask = mask.crop((x, y, x + w, y + h))
        bank.append((ch, mask))
    return bank


def _column_runs(strip: Image.Image) -> list[tuple[int, int]]:
    px = strip.load()
    ink = [any(px[x, y] < 128 for y in range(strip.height)) for x in range(strip.width)]
    runs: list[tuple[int, int]] = []
    i = 0
    n = len(ink)
    while i < n:
        if not ink[i]:
            i += 1
            continue
        j = i
        while j < n and ink[j]:
            j += 1
        runs.append((i, j))
        i = j
    return runs


def _classify_blob(glyph: Image.Image, bank: list[tuple[str, Image.Image]]) -> tuple[str, float]:
    pad = 3
    canvas = Image.new("L", (glyph.width + pad * 2, glyph.height + pad * 2), 255)
    canvas.paste(glyph, (pad, pad))
    best_ch, best_s = "", -1.0
    for ch, tmpl in bank:
        if ch == ",":
            continue
        tw, th = tmpl.size
        if tw > canvas.width or th > canvas.height:
            continue
        for ox in range(0, canvas.width - tw + 1):
            for oy in range(0, canvas.height - th + 1):
                s = _score(canvas, tmpl, ox, oy)
                if s > best_s:
                    best_s, best_ch = s, ch
    return best_ch, best_s


def _read_digits(mask: Image.Image, size: int = _AMT_SIZE, bold: bool = True) -> str:
    """Split the amount strip on empty columns, then match each ink blob."""
    bank = _digit_bank(size, bold)
    box = _ink_bbox(mask)
    if not box:
        return ""
    sx, sy, sw, sh = box
    strip = mask.crop((sx, sy, sx + sw, sy + sh))
    digit_h = max((t.size[1] for ch, t in bank if ch != ","), default=strip.height)
    out: list[str] = []
    for a, b in _column_runs(strip):
        blob = strip.crop((a, 0, b, strip.height))
        ink = _ink_bbox(blob)
        if not ink:
            continue
        bx, by, bw, bh = ink
        glyph = blob.crop((bx, by, bx + bw, by + bh))
        # comma / decimal sit low and short compared to a digit
        if bh < digit_h * 0.55 and by > strip.height * 0.30:
            out.append(",")
            continue
        ch, score = _classify_blob(glyph, bank)
        if ch and score >= 0.52:
            out.append(ch)
    return "".join(out)


def _contains_word(mask: Image.Image, word: str, size: int = _UI_SIZE, bold: bool = True) -> bool:
    tmpl = _binarize(_glyph(word, size, bold, fill=0, bg=255))
    box = _ink_bbox(tmpl)
    if box:
        x, y, w, h = box
        tmpl = tmpl.crop((x, y, x + w, y + h))
    if tmpl.width > mask.width or tmpl.height > mask.height:
        return False
    step_x = max(1, tmpl.width // 6)
    step_y = max(1, tmpl.height // 6)
    best = 0.0
    for y in range(0, mask.height - tmpl.height + 1, step_y):
        for x in range(0, mask.width - tmpl.width + 1, step_x):
            s = _score(mask, tmpl, x, y)
            if s > best:
                best = s
                if best >= 0.72:
                    return True
    return best >= 0.62


def _find_word(mask: Image.Image, word: str, size: int, bold: bool) -> dict | None:
    tmpl = _binarize(_glyph(word, size, bold))
    box = _ink_bbox(tmpl)
    if box:
        x, y, w, h = box
        tmpl = tmpl.crop((x, y, x + w, y + h))
    if tmpl.width > mask.width or tmpl.height > mask.height:
        return None
    step_x = max(1, tmpl.width // 5)
    step_y = max(1, tmpl.height // 4)
    best = (-1.0, 0, 0)
    for y in range(0, mask.height - tmpl.height + 1, step_y):
        for x in range(0, mask.width - tmpl.width + 1, step_x):
            s = _score(mask, tmpl, x, y)
            if s > best[0]:
                best = (s, x, y)
    if best[0] < 0.62:
        return None
    return {
        "text": word,
        "box": [best[1], best[2], tmpl.width, tmpl.height],
        "conf": float(best[0]),
    }


def read_text(img: Image.Image, psm: int = 6) -> str:
    """Return a space-joined guess of visible labels + digits. psm kept for callers."""
    del psm
    mask = _binarize(img)
    parts: list[str] = []
    for word, size, bold in (
        ("Submit", _UI_SIZE, True),
        ("Invoice", _UI_SIZE, True),
        ("Vendor", _UI_SIZE, True),
        ("Date", _UI_SIZE, True),
        ("Amount", _UI_SIZE, True),
        ("Ledger2005", _TITLE_SIZE, True),
    ):
        if _contains_word(mask, word, size, bold):
            parts.append(word)
    digits = _read_digits(mask, size=_AMT_SIZE, bold=True)
    if not digits:
        digits = _read_digits(mask, size=_UI_SIZE, bold=False)
    if digits:
        parts.append(digits)
    return " ".join(parts)


def word_boxes(img: Image.Image) -> list[dict]:
    mask = _binarize(img)
    out: list[dict] = []
    for word, size, bold in (
        ("Submit", _UI_SIZE, True),
        ("Invoice", _UI_SIZE, True),
        ("Vendor", _UI_SIZE, True),
        ("Date", _UI_SIZE, True),
        ("Amount", _UI_SIZE, True),
        ("Ledger2005", _TITLE_SIZE, True),
    ):
        hit = _find_word(mask, word, size, bold)
        if hit:
            out.append(hit)
    return out


def parse_amount(text: str) -> int | None:
    if not text:
        return None
    digits = re.sub(r"[^0-9]", "", text)
    return int(digits) if digits else None


def amount_from_region(img: Image.Image, box: tuple[int, int, int, int] | list[int]) -> tuple[int | None, str]:
    """Amount from pixels only. Pillow templates — never Tesseract, never an LLM."""
    region = crop_box(img, box)
    if region.width > 16 and region.height > 16:
        region = region.crop((4, 4, region.width - 4, region.height - 4))
    mask = _binarize(region)
    text = _read_digits(mask, size=_AMT_SIZE, bold=True) or _read_digits(mask, size=_UI_SIZE, bold=True)
    digits = re.sub(r"[^0-9]", "", text)
    return (int(digits) if digits else None), text
