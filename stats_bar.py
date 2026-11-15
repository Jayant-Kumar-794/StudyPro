"""StatsBar.tsx: Total / Completed / Pending cards and the Overall Progress card."""
import tkinter as tk

from .. import gfx
from ..theme import C, F, sc
from ..widgets import draw_progress
from .cards import CardCanvas


class StatCard(CardCanvas):
    def __init__(self, parent, label, icon, color):
        super().__init__(parent)
        self.label, self.icon, self.color, self.value = label, icon, color, 0

    def content_height(self, w):
        return sc(1 + 16 + 24 + 8 + 32 + 16 + 16 + 1)          # p-4, icon, mb-2, text-2xl, text-xs

    def draw_content(self, x1, y1, x2, y2):
        cx = (x1 + x2) // 2
        y = y1 + sc(16)
        self.create_image(cx, y + sc(12), image=gfx.icon(self.icon, sc(24), self.color), tags="d")
        y += sc(24 + 8)
        self.create_text(cx, y + sc(16), text=str(self.value), font=F(24, "bold"), fill=C["card_fg"], tags="d")
        y += sc(32)
        self.create_text(cx, y + sc(8), text=self.label, font=F(12), fill=C["muted_fg"], tags="d")


class ProgressCard(CardCanvas):
    def __init__(self, parent):
        super().__init__(parent)
        self.value = 0

    def content_height(self, w):
        return sc(1 + 16 + 20 + 8 + 10 + 16 + 1)

    def draw_content(self, x1, y1, x2, y2):
        x1, x2 = x1 + sc(16), x2 - sc(16)
        y = y1 + sc(16)
        self.create_text(x1, y + sc(10), anchor="w", text="Overall Progress", font=F(14), fill=C["muted_fg"],
                         tags="d")
        self.create_text(x2, y + sc(10), anchor="e", text="%d%%" % self.value, font=F(14, "semibold"),
                         fill=C["card_fg"], tags="d")
        y += sc(28)
        draw_progress(self, x1, y, x2, sc(10), self.value, tags="d")


class StatsBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["background"])
        row = tk.Frame(self, bg=C["background"])
        row.pack(fill="x")
        self.cards = [StatCard(row, "Total", "list-todo", C["primary"]),
                      StatCard(row, "Completed", "circle-check-big", C["low"]),
                      StatCard(row, "Pending", "clock", C["medium"])]
        for i, c in enumerate(self.cards):
            row.columnconfigure(i, weight=1, uniform="s")
            c.grid(row=0, column=i, sticky="nsew")
        self.progress = ProgressCard(self)
        self.progress.pack(fill="x")          # 8 + 8 margins = space-y-4

    def update(self, tasks):
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "completed")
        for card, v in zip(self.cards, (total, done, total - done)):
            card.value = v
            card.redraw()
        self.progress.value = int(done * 100.0 / total + 0.5) if total else 0
        self.progress.redraw()
