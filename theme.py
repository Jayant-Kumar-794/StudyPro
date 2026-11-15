"""Design tokens copied from the web version (src/index.css + tailwind.config.ts).

Colours are defined exactly as the CSS HSL variables, fonts use Inter (bundled in assets/fonts),
and every size is written in CSS pixels and scaled with sc() for high-DPI screens.
"""
import colorsys
import os
import sys
import tkinter as tk
import tkinter.font as tkfont

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def hsl(h, s, l, a=None):
    """CSS hsl(h s% l%) -> '#rrggbb'.  With a (0..1) the colour is returned as (hex, alpha)."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    col = "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))
    return (col, a) if a is not None else col


# ---------------------------------------------------------------- :root variables (light theme)
C = {
    "background": hsl(220, 20, 97),
    "foreground": hsl(224, 30, 15),
    "card": hsl(0, 0, 100),
    "card_fg": hsl(224, 30, 15),
    "popover": hsl(0, 0, 100),
    "primary": hsl(230, 80, 56),
    "primary_fg": hsl(0, 0, 100),
    "secondary": hsl(220, 20, 94),
    "muted": hsl(220, 15, 92),
    "muted_fg": hsl(220, 10, 46),
    "accent": hsl(250, 70, 60),
    "accent_fg": hsl(0, 0, 100),
    "destructive": hsl(0, 72, 51),
    "border": hsl(220, 15, 88),
    "input": hsl(220, 15, 88),
    "ring": hsl(230, 80, 56),
    "high": hsl(0, 72, 51),
    "medium": hsl(25, 95, 53),
    "low": hsl(142, 71, 45),
    "hero_end": hsl(280, 70, 55),          # .gradient-hero second stop
    "white": "#ffffff",
    "black": "#000000",
}
RADIUS = 12                                 # --radius: 0.75rem
R_LG, R_MD, R_SM = RADIUS, RADIUS - 2, RADIUS - 4


def to_rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in rgb)


def mix(a, b, t):
    """Colour between a (t=0) and b (t=1)."""
    ra, rb = to_rgb(a), to_rgb(b)
    return to_hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def alpha(color, a, over):
    """CSS colour with alpha a painted over the colour 'over' (e.g. bg-primary/10 on a white card)."""
    return mix(over, color, a)


def gradient_at(t, start=None, end=None):
    return mix(start or C["primary"], end or C["accent"], max(0.0, min(1.0, t)))


# ---------------------------------------------------------------- DPI scaling
_S = [1.0]


def init_scaling(root):
    """Scale factor of the screen (1.0 at 96 DPI / 100 %)."""
    forced = os.environ.get("STUDYPRO_SCALE")
    if forced:
        _S[0] = float(forced)
        return _S[0]
    try:
        _S[0] = max(1.0, root.winfo_fpixels("1i") / 96.0)
    except tk.TclError:
        _S[0] = 1.0
    return _S[0]


def sc(px):
    return int(round(px * _S[0]))


def scale():
    return _S[0]


# ---------------------------------------------------------------- fonts
_FAMILY = {"regular": "Inter", "medium": "Inter Medium", "semibold": "Inter SemiBold", "bold": "Inter"}
_fonts = {}
_FONT_FILES = ["Inter-Regular.otf", "Inter-Medium.otf", "Inter-SemiBold.otf", "Inter-Bold.otf"]


def register_fonts():
    """Make the bundled Inter font available to this program only (Windows), no installation needed."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        FR_PRIVATE = 0x10
        for f in _FONT_FILES:
            path = os.path.join(ASSETS, "fonts", f)
            if os.path.exists(path):
                ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0)
    except Exception:
        pass


def init_fonts(root):
    """Choose Inter when it is available, otherwise a similar system font."""
    fams = set(tkfont.families(root))
    if "Inter" not in fams:
        fallback = next((f for f in ("Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans") if f in fams), "TkDefaultFont")
        for k in _FAMILY:
            _FAMILY[k] = fallback
    else:
        for k, fam in (("medium", "Inter Medium"), ("semibold", "Inter SemiBold")):
            if fam not in fams:
                _FAMILY[k] = "Inter"


def F(px, weight="regular", strike=False, underline=False):
    """Font of px CSS pixels. weight: regular 400 / medium 500 / semibold 600 / bold 700."""
    key = (px, weight, strike, underline, _S[0])
    if key not in _fonts:
        fam = _FAMILY[weight]
        bold = "bold" if weight == "bold" or (weight == "semibold" and fam == _FAMILY["regular"]) else "normal"
        _fonts[key] = tkfont.Font(family=fam, size=-sc(px), weight=bold, overstrike=int(strike),
                                  underline=int(underline))
    return _fonts[key]


def text_width(text, font):
    return font.measure(text)


def ellipsize(text, font, width):
    """Cut text to fit width with an ellipsis (CSS 'truncate')."""
    if font.measure(text) <= width:
        return text
    while text and font.measure(text + "…") > width:
        text = text[:-1]
    return text + "…"
