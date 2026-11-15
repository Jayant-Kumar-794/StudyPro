"""Anti-aliased graphics for tkinter, in pure Python (no Pillow).

tkinter draws canvas shapes without anti-aliasing on Windows, so rounded corners, circles and
icons would look jagged. Here they are rendered as small transparent PNG images instead
(a tiny PNG encoder + coverage-based anti-aliasing) and cached, so every shape is smooth like
in the browser.
"""
import base64
import math
import struct
import tkinter as tk
import zlib

from .icon_data import ICONS
from .theme import to_rgb, sc, scale

_cache = {}


# ------------------------------------------------------------------ PNG encoder
def _png(w, h, rows):
    """rows: list of bytearrays with w*4 RGBA bytes."""
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def photo(key, w, h, rows):
    if key not in _cache:
        _cache[key] = tk.PhotoImage(data=base64.b64encode(_png(w, h, rows)), format="png")
    return _cache[key]


def _clamp(v):
    return 0.0 if v < 0 else (1.0 if v > 1 else v)


# ------------------------------------------------------------------ rounded corners and circles
def corner(r, fill, border=None, bw=1, quadrant="tl", fill_alpha=1.0):
    """r x r image of one rounded corner (fill + optional border), transparent outside."""
    key = ("corner", r, fill, border, bw, quadrant, fill_alpha)
    if key in _cache:
        return _cache[key]
    fr, fg, fb = to_rgb(fill) if fill else (0, 0, 0)
    br_, bg_, bb_ = to_rgb(border) if border else (0, 0, 0)
    rows = []
    for y in range(r):
        row = bytearray()
        for x in range(r):
            px = x + 0.5 if quadrant in ("tr", "br") else r - x - 0.5
            py = y + 0.5 if quadrant in ("bl", "br") else r - y - 0.5
            d = math.hypot(px, py)
            outer = _clamp(r + 0.5 - d) if (px > 0 or py > 0) else 1.0
            if border:
                inner = _clamp(r - bw + 0.5 - d)
                cb, cf = outer - inner, inner * (fill_alpha if fill else 0)
            else:
                cb, cf = 0.0, outer * fill_alpha
            a = cb + cf
            if a <= 0:
                row += b"\x00\x00\x00\x00"
                continue
            row += bytes((round((br_ * cb + fr * cf) / a), round((bg_ * cb + fg * cf) / a),
                          round((bb_ * cb + fb * cf) / a), round(min(1, a) * 255)))
        rows.append(row)
    return photo(key, r, r, rows)


def circle(d, fill=None, border=None, bw=1.0):
    """d x d anti-aliased circle (filled and/or outlined)."""
    key = ("circle", d, fill, border, bw)
    if key in _cache:
        return _cache[key]
    R = d / 2.0
    fr, fg, fb = to_rgb(fill) if fill else (0, 0, 0)
    br_, bg_, bb_ = to_rgb(border) if border else (0, 0, 0)
    rows = []
    for y in range(d):
        row = bytearray()
        for x in range(d):
            dist = math.hypot(x + 0.5 - R, y + 0.5 - R)
            outer = _clamp(R + 0.5 - dist - 0.5)
            inner = _clamp(R - bw + 0.5 - dist - 0.5) if border else outer
            cb = (outer - inner) if border else 0.0
            cf = inner if fill else 0.0
            a = cb + cf
            if a <= 0:
                row += b"\x00\x00\x00\x00"
                continue
            row += bytes((round((br_ * cb + fr * cf) / a), round((bg_ * cb + fg * cf) / a),
                          round((bb_ * cb + fb * cf) / a), round(min(1, a) * 255)))
        rows.append(row)
    return photo(key, d, d, rows)


# ------------------------------------------------------------------ icons
def _segments(name, s, angle=0.0):
    segs = []
    ca, sa = math.cos(angle), math.sin(angle)
    for line in ICONS[name]:
        pts = []
        for i in range(0, len(line), 2):
            x, y = line[i] - 12, line[i + 1] - 12
            if angle:
                x, y = x * ca - y * sa, x * sa + y * ca
            pts.append(((x + 12) * s, (y + 12) * s))
        segs += list(zip(pts, pts[1:]))
    return segs


def icon(name, size, color, stroke=2.0, angle=0.0):
    """Lucide icon as a size x size transparent image (size already in screen pixels)."""
    key = ("icon", name, size, color, stroke, round(angle, 3))
    if key in _cache:
        return _cache[key]
    s = size / 24.0
    hw = stroke * s / 2.0
    segs = _segments(name, s, angle)
    INF = 1e9
    dist = [[INF] * size for _ in range(size)]
    for (x1, y1), (x2, y2) in segs:
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy or 1e-9
        x0 = max(0, int(min(x1, x2) - hw - 1.5)); xe = min(size, int(max(x1, x2) + hw + 2.5))
        y0 = max(0, int(min(y1, y2) - hw - 1.5)); ye = min(size, int(max(y1, y2) + hw + 2.5))
        for py in range(y0, ye):
            cy = py + 0.5
            drow = dist[py]
            for px in range(x0, xe):
                cx = px + 0.5
                t = ((cx - x1) * dx + (cy - y1) * dy) / L2
                t = 0.0 if t < 0 else (1.0 if t > 1 else t)
                ex, ey = x1 + t * dx - cx, y1 + t * dy - cy
                dd = ex * ex + ey * ey
                if dd < drow[px]:
                    drow[px] = dd
    r, g, b = to_rgb(color)
    rows = []
    for py in range(size):
        row = bytearray()
        for px in range(size):
            a = _clamp(hw + 0.5 - math.sqrt(dist[py][px]))
            row += bytes((r, g, b, round(a * 255)))
        rows.append(row)
    return photo(key, size, size, rows)


# ------------------------------------------------------------------ gradients
def gradient_box(w, h, r, c1, c2, opacity=1.0, angle=135):
    """Rounded rectangle filled with a CSS linear-gradient(angle, c1, c2), as one image."""
    key = ("grad", w, h, r, c1, c2, opacity, angle)
    if key in _cache:
        return _cache[key]
    a = math.radians(angle)
    vx, vy = math.sin(a), -math.cos(a)                      # CSS gradient direction
    L = abs(w * vx) + abs(h * vy)
    r1, g1, b1 = to_rgb(c1)
    r2, g2, b2 = to_rgb(c2)
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            t = _clamp(((x + 0.5 - w / 2.0) * vx + (y + 0.5 - h / 2.0) * vy) / L + 0.5)
            cov = 1.0
            if r:
                cx = r if x < r else (w - r if x >= w - r else x + 0.5)
                cy = r if y < r else (h - r if y >= h - r else y + 0.5)
                if (x < r or x >= w - r) and (y < r or y >= h - r):
                    cov = _clamp(r + 0.5 - math.hypot(x + 0.5 - cx, y + 0.5 - cy))
            row += bytes((round(r1 + (r2 - r1) * t), round(g1 + (g2 - g1) * t), round(b1 + (b2 - b1) * t),
                          round(cov * opacity * 255)))
        rows.append(row)
    return photo(key, w, h, rows)


def gradient_lines(canvas, w, h, c1, c2, tag="grad", step=2):
    """Fill a whole canvas with a 135deg gradient using diagonal lines (fast for big areas)."""
    canvas.delete(tag)
    n = w + h
    r1, g1, b1 = to_rgb(c1)
    r2, g2, b2 = to_rgb(c2)
    for k in range(0, n + step, step):
        t = k / float(n)
        col = "#%02x%02x%02x" % (round(r1 + (r2 - r1) * t), round(g1 + (g2 - g1) * t), round(b1 + (b2 - b1) * t))
        canvas.create_line(k, 0, k - h - 1, h + 1, fill=col, width=step + 1, tags=tag)
    canvas.tag_lower(tag)


# ------------------------------------------------------------------ composite: rounded box on a canvas
def draw_box(cv, x1, y1, x2, y2, r, fill, border=None, bw=1, tags=(), fill_alpha_over=None):
    """Rounded rectangle with anti-aliased corners: rectangles for the body, images for the corners."""
    x1, y1, x2, y2 = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))
    r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    ids = []
    if r == 0:
        ids.append(cv.create_rectangle(x1, y1, x2 - 1, y2 - 1, fill=fill or "", outline=border or "",
                                       width=bw if border else 0, tags=tags))
        return ids
    if fill:
        ids.append(cv.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", width=0, tags=tags))
        ids.append(cv.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", width=0, tags=tags))
    if border:
        for (ax, ay, bx, by) in ((x1 + r, y1, x2 - r, y1 + bw), (x1 + r, y2 - bw, x2 - r, y2),
                                 (x1, y1 + r, x1 + bw, y2 - r), (x2 - bw, y1 + r, x2, y2 - r)):
            ids.append(cv.create_rectangle(ax, ay, bx, by, fill=border, outline="", width=0, tags=tags))
    for q, (cx, cy) in (("tl", (x1, y1)), ("tr", (x2 - r, y1)), ("bl", (x1, y2 - r)), ("br", (x2 - r, y2 - r))):
        ids.append(cv.create_image(cx, cy, image=corner(r, fill, border, bw, q), anchor="nw", tags=tags))
    return ids


def draw_shadow(cv, x1, y1, x2, y2, r, bg, color, strength=0.08, dy=4, blur=16, tags=()):
    """Soft CSS-like box shadow: layered rounded rectangles blended into the background."""
    from .theme import mix
    steps = 6
    for i in range(steps, 0, -1):
        grow = blur * i / steps - 4
        a = strength * (1 - i / (steps + 1.0)) * 0.9
        col = mix(bg, color, a)
        draw_box(cv, x1 - grow, y1 - grow + dy, x2 + grow, y2 + grow + dy, int(r + grow) if r + grow > 0 else 0,
                 col, tags=tags)


def corner_mask(r, color, quadrant="tl"):
    """r x r image that is 'color' OUTSIDE a rounded corner and transparent inside (for overflow-hidden)."""
    key = ("cmask", r, color, quadrant)
    if key in _cache:
        return _cache[key]
    cr, cg, cb = to_rgb(color)
    rows = []
    for y in range(r):
        row = bytearray()
        for x in range(r):
            px = x + 0.5 if quadrant in ("tr", "br") else r - x - 0.5
            py = y + 0.5 if quadrant in ("bl", "br") else r - y - 0.5
            a = 1.0 - _clamp(r + 0.5 - math.hypot(px, py))
            row += bytes((cr, cg, cb, round(a * 255)))
        rows.append(row)
    return photo(key, r, r, rows)


def round_corners(cv, x1, y1, x2, y2, r, outside, tags=()):
    """Cut rounded corners into whatever is drawn in the rectangle (CSS rounded-* + overflow-hidden)."""
    for q, (cx, cy) in (("tl", (x1, y1)), ("tr", (x2 - r, y1)), ("bl", (x1, y2 - r)), ("br", (x2 - r, y2 - r))):
        cv.create_image(cx, cy, image=corner_mask(r, outside, q), anchor="nw", tags=tags)


def alpha_box(w, h, r, color, a):
    """Rounded box of a colour with opacity (e.g. bg-white/20 on the gradient navbar)."""
    return gradient_box(w, h, r, color, color, a)
