"""ExamSection.tsx: upcoming exams with countdown badges and the 'Add Exam' dialog."""
import tkinter as tk

from .. import gfx, store
from ..theme import C, F, sc, alpha
from ..widgets import Dialog, Input, DateInput, Button, FieldLabel, CvButton, draw_badge
from .cards import CardCanvas


class SectionHeader(tk.Canvas):
    """<h2 class='text-lg font-bold flex items-center gap-2'><Icon class='w-5 h-5 text-primary'/> Title</h2>"""

    def __init__(self, parent, icon, title):
        super().__init__(parent, height=sc(36), bg=C["background"], highlightthickness=0, bd=0, width=10)
        self.create_image(0, sc(18), anchor="w", image=gfx.icon(icon, sc(20), C["primary"]))
        self.create_text(sc(28), sc(18), anchor="w", text=title, font=F(18, "bold"), fill=C["foreground"])


class ExamCard(CardCanvas):
    def __init__(self, parent, section, exam, nearest):
        super().__init__(parent, lift=2, margin=6)        # gap-3
        self.section, self.exam, self.nearest = section, exam, nearest
        self.days = store.calc_days_left(exam["examDate"])
        self.urgent = 0 <= self.days <= 3
        self.btn = CvButton(self, icon="trash-2", command=lambda: section.delete(exam), fg=C["muted_fg"],
                            hover_fg=C["destructive"])

    def content_height(self, w):
        return sc(1 + 16 + 44 + 8 + 22 + 16 + 1)

    def border_color(self):
        if self.urgent:
            return alpha(C["high"], 0.4, C["card"])
        if self.nearest:
            return alpha(C["primary"], 0.4, C["card"])
        return C["border"]

    def ring_color(self):
        return alpha(C["high"], 0.2, C["background"]) if self.urgent else None

    def draw_content(self, x1, y1, x2, y2):
        X1, X2, y = x1 + sc(16), x2 - sc(16), y1 + sc(16)
        e, d = self.exam, self.days
        self.create_text(X1, y + sc(12), anchor="w", text=e["subject"], font=F(16, "semibold"), fill=C["card_fg"],
                         tags="d")
        self.create_text(X1, y + sc(24 + 10), anchor="w", text=store.us_date(e["examDate"]), font=F(14),
                         fill=C["muted_fg"], tags="d")
        self.btn.place(X2 - self.btn.w, y)
        y += sc(44 + 8)
        x = X1
        badges = []
        if self.urgent:
            badges.append(("Today!" if d <= 0 else "%d day%s" % (d, "s" if d > 1 else ""), C["high"],
                           alpha(C["high"], 0.1, C["card"]), alpha(C["high"], 0.3, C["card"]), "triangle-alert"))
        if not self.urgent and d >= 0:
            badges.append(("%d day%s away" % (d, "" if d == 1 else "s"), C["foreground"], C["card"], C["border"], None))
        if d < 0:
            badges.append(("Passed", C["muted_fg"], C["card"], C["border"], None))
        if self.nearest and d >= 0:
            badges.append(("Next", C["primary"], alpha(C["primary"], 0.1, C["card"]),
                           alpha(C["primary"], 0.3, C["card"]), None))
        for text, fg, fill, border, icon in badges:
            x += draw_badge(self, x, y, text, fg, fill, border, icon, tags="d") + sc(8)


class ExamSection(tk.Frame):
    def __init__(self, parent, dash):
        super().__init__(parent, bg=C["background"])
        self.dash = dash
        head = tk.Frame(self, bg=C["background"])
        head.pack(fill="x", padx=sc(8), pady=(0, sc(8)))
        Button(head, "Add Exam", self.open_dialog, size="sm", icon="plus", icon_gap=12,
               bg=C["background"]).pack(side="right")
        SectionHeader(head, "graduation-cap", "Upcoming Exams").pack(side="left", fill="x", expand=True)
        self.grid_frame = None

    def render(self, exams, cols):
        if self.grid_frame is not None:
            self.grid_frame.destroy()
        g = self.grid_frame = tk.Frame(self, bg=C["background"])
        g.pack(fill="x", padx=sc(2), pady=(sc(2), 0))
        ex = sorted(exams, key=lambda e: store.parse_local_date(e["examDate"]))
        if not ex:
            tk.Label(g, text="No exams scheduled", font=F(14), fg=C["muted_fg"], bg=C["background"]).pack(
                pady=sc(24 + 8))
            return
        for i in range(cols):
            g.columnconfigure(i, weight=1, uniform="e")
        for i, e in enumerate(ex):
            card = ExamCard(g, self, e, i == 0)
            card.grid(row=i // cols, column=i % cols, sticky="nsew")

    def delete(self, exam):
        store.delete_exam(exam["userId"], exam["id"])
        self.dash.load_all()

    def open_dialog(self):
        ExamDialog(self.dash.app, self.dash)


class ExamDialog(Dialog):
    def __init__(self, app, dash):
        super().__init__(app, "Add Exam", width=384)
        self.dash = dash
        b, bg, P = self.body, C["background"], sc(4)
        FieldLabel(b, "Subject", bg).pack(fill="x", padx=P)
        self.subject = Input(b, placeholder="e.g. Physics", bg=bg, on_enter=self.submit)
        self.subject.pack(fill="x", pady=(P, 0))
        FieldLabel(b, "Exam Date", bg).pack(fill="x", padx=P, pady=(sc(12), 0))
        self.date = DateInput(b, bg=bg)
        self.date.entry.bind("<Return>", lambda e: (self.submit(), "break")[1])
        self.date.pack(fill="x", pady=(P, 0))
        btns = tk.Frame(b, bg=bg)
        btns.pack(fill="x", padx=P, pady=(sc(12), 0))
        Button(btns, "Add", self.submit, variant="gradient", bg=bg).pack(side="right")
        Button(btns, "Cancel", self.close, variant="outline", bg=bg).pack(side="right", padx=(0, sc(8)))
        self.show(focus=self.subject.focus)

    def submit(self):
        subject, d = self.subject.get().strip(), self.date.value()
        if not subject or not d:
            return
        store.add_exam(self.dash.user["id"], subject, d.isoformat())
        self.close()
        self.dash.load_all()
