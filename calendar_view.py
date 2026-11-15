"""CalendarView.tsx: month grid (Mon..Sun) with task deadlines and exam dates."""
import calendar
import datetime as dt
import tkinter as tk

from .. import gfx, store
from ..models import CalendarService
from ..theme import C, F, sc, alpha, ellipsize, R_LG
from ..widgets import Button
from .exam_section import SectionHeader


class CalendarGrid(tk.Canvas):
    def __init__(self, parent, view):
        super().__init__(parent, bg=C["background"], highlightthickness=0, bd=0, height=100, width=10)
        self.view = view
        self.bind("<Configure>", lambda e: self.draw())

    def layout(self, W):
        v = self.view
        first = dt.date(v.year, v.month, 1)
        offset = first.weekday()                       # Monday = 0
        n = calendar.monthrange(v.year, v.month)[1]
        cells = [None] * offset + list(range(1, n + 1))
        rows = [cells[i:i + 7] for i in range(0, len(cells), 7)]
        heights = []
        for r in rows:
            h = sc(70)
            for d in r:
                if d and len(v.events.get(self._key(d), [])) > 2:
                    h = max(h, sc(6 + 16 + 4) + 2 * sc(16) + sc(2) * 2 + sc(13) + sc(6))
            heights.append(h)
        return rows, heights

    def _key(self, d):
        return "%04d-%02d-%02d" % (self.view.year, self.view.month, d)

    def required_height(self, W):
        rows, heights = self.layout(W)
        return sc(32) + 1 + sum(heights) + len(rows)

    def draw(self):
        self.delete("all")
        W = self.winfo_width()
        if W < 50:
            return
        v = self.view
        rows, heights = self.layout(W)
        H = self.required_height(W)
        if int(self.cget("height")) != H:
            self.configure(height=H)
        gap = 1
        cw = (W - 6 * gap) / 7.0
        self.create_rectangle(0, 0, W, H, fill=C["border"], outline="")          # bg-border shows in the gaps
        for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            x = i * (cw + gap)
            self.create_rectangle(x, 0, x + cw, sc(32), fill=C["muted"], outline="")
            self.create_text(x + cw / 2, sc(16), text=name, font=F(12, "semibold"), fill=C["muted_fg"])
        today = store.today()
        y = sc(32) + gap
        for r, row in enumerate(rows):
            h = heights[r]
            for i, d in enumerate(row):
                x = i * (cw + gap)
                self.create_rectangle(x, y, x + cw, y + h, fill=C["card"], outline="")
                if d is None:
                    continue
                cx, cy = x + sc(6), y + sc(6)
                is_today = dt.date(v.year, v.month, d) == today
                if is_today:                        # ring-2 ring-primary ring-inset
                    self.create_rectangle(x + 1, y + 1, x + cw - 1, y + h - 1, outline=C["primary"], width=2)
                    self.create_image(cx, cy - sc(2), anchor="nw", image=gfx.circle(sc(20), C["primary"]))
                    self.create_text(cx + sc(10), cy + sc(8), text=str(d), font=F(12, "medium"), fill=C["primary_fg"])
                    ey = cy + sc(20) + sc(4) - sc(2)
                else:
                    self.create_text(cx, cy + sc(8), anchor="w", text=str(d), font=F(12, "medium"), fill=C["card_fg"])
                    ey = cy + sc(16) + sc(4)
                evs = v.events.get(self._key(d), [])
                for ev in evs[:2]:
                    if ev["urgent"]:
                        fg, bg = C["high"], alpha(C["high"], 0.15, C["card"])
                    elif ev["type"] == "exam":
                        fg, bg = C["primary"], alpha(C["primary"], 0.1, C["card"])
                    else:
                        fg, bg = C["low"], alpha(C["low"], 0.1, C["card"])
                    gfx.draw_box(self, cx, ey, x + cw - sc(6), ey + sc(16), sc(4), bg)
                    self.create_text(cx + sc(4), ey + sc(8), anchor="w", font=F(10), fill=fg,
                                     text=ellipsize(ev["label"], F(10), cw - sc(12) - sc(8)))
                    ey += sc(16) + sc(2)
                if len(evs) > 2:
                    self.create_text(cx, ey + sc(6), anchor="w", text="+%d" % (len(evs) - 2), font=F(10),
                                     fill=C["muted_fg"])
            y += h + gap
        gfx.round_corners(self, 0, 0, W, H, sc(R_LG), C["background"])           # rounded-xl overflow-hidden


class CalendarView(tk.Frame):
    def __init__(self, parent, dash):
        super().__init__(parent, bg=C["background"])
        today = store.today()
        self.year, self.month = today.year, today.month
        self.events = {}
        bg = C["background"]
        head = tk.Frame(self, bg=bg)
        head.pack(fill="x", padx=sc(8))
        nav = tk.Frame(head, bg=bg)
        nav.pack(side="right")
        Button(nav, "", self.prev, variant="ghost", size="sm", icon="chevron-left", bg=bg).pack(side="left")
        self.month_lbl = tk.Canvas(nav, width=sc(140), height=sc(36), bg=bg, highlightthickness=0, bd=0)
        self.month_lbl.pack(side="left", padx=sc(8))
        Button(nav, "", self.next, variant="ghost", size="sm", icon="chevron-right", bg=bg).pack(side="left")
        SectionHeader(head, "calendar-days", "Calendar").pack(side="left", fill="x", expand=True)
        legend = tk.Canvas(self, height=sc(16), bg=bg, highlightthickness=0, bd=0)
        legend.pack(fill="x", padx=sc(8), pady=(sc(16), 0))
        x = 0
        for label, col in (("Exam", C["primary"]), ("Assignment", C["low"]), ("Urgent", C["high"])):
            legend.create_image(x, sc(8), anchor="w", image=gfx.circle(sc(10), col))
            legend.create_text(x + sc(14), sc(8), anchor="w", text=label, font=F(12), fill=C["foreground"])
            x += sc(14) + F(12).measure(label) + sc(16)
        self.grid_cv = CalendarGrid(self, self)
        self.grid_cv.pack(fill="x", padx=sc(8), pady=(sc(16), 0))

    def render(self, tasks, exams):
        self.events = {}
        for ev in CalendarService().render_calendar(tasks, exams):
            self.events.setdefault(ev["date"], []).append(ev)
        self.draw()

    def draw(self):
        lb = self.month_lbl
        lb.delete("all")
        lb.create_text(sc(70), sc(18), text=dt.date(self.year, self.month, 1).strftime("%B %Y"),
                       font=F(14, "semibold"), fill=C["foreground"])
        self.grid_cv.draw()

    def prev(self):
        self.month -= 1
        if self.month == 0:
            self.month, self.year = 12, self.year - 1
        self.draw()

    def next(self):
        self.month += 1
        if self.month == 13:
            self.month, self.year = 1, self.year + 1
        self.draw()
