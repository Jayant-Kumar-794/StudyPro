"""Card base class: bg-card rounded-xl border shadow-card (+ hover:shadow-card-hover hover:-translate-y-1).

Every card is one Canvas with an 8 px margin around it, in which the soft shadow is drawn and the card
can move up on hover. Grids of cards therefore use 0 px gaps between the canvases (8 + 8 = gap-4).
"""
import tkinter as tk

from .. import gfx
from ..theme import C, sc, mix, R_LG
from ..widgets import HoverWatch

M = 8                                   # CSS px of margin around a card canvas


def ease(t):
    return 1 - (1 - t) ** 3


class CardCanvas(tk.Canvas):
    radius = R_LG

    def __init__(self, parent, page_bg=None, lift=0, fade=1.0, margin=M):
        self.page_bg = page_bg or C["background"]
        super().__init__(parent, bg=self.page_bg, highlightthickness=0, bd=0, width=sc(100), height=sc(100))
        self.m = sc(margin)
        self.lift_px = sc(lift)
        self.fade = fade
        self.t = 0.0                    # 0 = normal, 1 = hovered (animated)
        self.hover = False
        self._anim = None
        self._req_h = None
        self.bind("<Configure>", self._on_cfg)
        if lift:
            HoverWatch(self, self._set_hover)

    # colour helper for opacity-70 cards -----------------------------------------
    def c(self, col):
        return mix(self.page_bg, col, self.fade) if self.fade < 1 else col

    # sizing ----------------------------------------------------------------------
    def content_height(self, width):
        """Height of the card (CSS box incl. border) for this outer width. Override."""
        return sc(100)

    def _on_cfg(self, e):
        W = self.winfo_width()
        h = self.content_height(W - 2 * self.m) + 2 * self.m
        if h != self._req_h:
            self._req_h = h
            self.configure(height=h)
        self.redraw()

    # hover animation ---------------------------------------------------------------
    def _set_hover(self, v):
        self.hover = v
        self.on_hover(v)
        if self._anim is None:
            self._anim = self.after(16, self._step)

    def on_hover(self, v):
        pass

    def _step(self):
        self._anim = None
        target = 1.0 if self.hover else 0.0
        if abs(self.t - target) < 1e-3:
            return
        self.t = min(1.0, self.t + 0.2) if self.hover else max(0.0, self.t - 0.2)
        self.redraw()
        self._anim = self.after(16, self._step)

    # drawing -----------------------------------------------------------------------
    def border_color(self):
        return C["border"]

    def ring_color(self):
        return None

    def redraw(self):
        self.delete("d")
        W, H = self.winfo_width(), self.winfo_height()
        if W < 20 or H < 20:
            return
        m = self.m
        k = ease(self.t)
        dy = -int(round(self.lift_px * k))
        x1, y1, x2, y2 = m, m + dy, W - m, H - m + dy
        r = sc(self.radius)
        # shadow-card -> shadow-card-hover
        gfx.draw_shadow(self, x1, y1, x2, y2, r, self.page_bg, self.c(C["primary"]),
                        strength=0.07 + 0.08 * k, dy=sc(4) + int(sc(4) * k), blur=sc(10), tags="d")
        ring = self.ring_color()
        if ring:                         # ring-1 ring-priority-high/20 (outside the border)
            gfx.draw_box(self, x1 - 1, y1 - 1, x2 + 1, y2 + 1, r + 1, self.c(ring), tags="d")
        gfx.draw_box(self, x1, y1, x2, y2, r, self.c(C["card"]), self.c(self.border_color()), tags="d")
        self.draw_content(x1 + 1, y1 + 1, x2 - 1, y2 - 1)
        self.tag_raise("btn")

    def draw_content(self, x1, y1, x2, y2):
        pass
