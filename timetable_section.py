"""TimetableSection.tsx: weekly class table (Mon..Sun) and the 'Add Class' dialog."""
import tkinter as tk

from .. import gfx, store
from ..theme import C, F, sc, alpha, R_LG
from ..widgets import Dialog, Input, Select, Button, FieldLabel
from .exam_section import SectionHeader

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ENTRY_H, ENTRY_GAP = 46, 6


class TimetableTable(tk.Canvas):
    def __init__(self, parent, section):
        super().__init__(parent, bg=C["background"], highlightthickness=0, bd=0, height=100, width=10)
        self.section = section
        self.grouped = {d: [] for d in DAYS}
        self.hover = None          # (entry id, over the trash icon?)
        self.boxes = []            # (x1, y1, x2, y2, entry)
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))
        self.bind("<ButtonRelease-1>", self._click)

    def set_entries(self, entries):
        self.grouped = {d: [] for d in DAYS}
        for e in entries:
            self.grouped.setdefault(e["day"], []).append(e)
        for d in self.grouped:                      # sorted by the real start time
            self.grouped[d].sort(key=lambda e: store.time_slot_key(e["timeSlot"]))
        self.draw()

    def col_widths(self, W):
        """CSS automatic table layout: every column gets max(min-w-[120px], content); the free space is shared
        in proportion to the content widths."""
        f1, f2 = F(12, "medium"), F(11)
        maxc = []
        for d in DAYS:
            w = F(14, "semibold").measure(d) + sc(24)
            for e in self.grouped[d]:
                w = max(w, max(f1.measure(e["subject"]), f2.measure(e["timeSlot"])) + sc(16) + sc(16) + 1)
            if not self.grouped[d]:
                w = max(w, F(12).measure("—") + sc(16) + 1)
            maxc.append(w)
        base = [max(sc(120), w) for w in maxc]
        extra = W - sum(base)
        tot = float(sum(maxc))
        return [b + extra * m / tot for b, m in zip(base, maxc)] if extra > 0 else base

    def body_height(self):
        n = max([len(v) for v in self.grouped.values()] + [0])
        inner = sc(n * ENTRY_H + max(0, n - 1) * ENTRY_GAP) if n else sc(16)
        return sc(8) + inner + sc(8)

    def draw(self):
        self.delete("all")
        W = self.winfo_width()
        if W < 50:
            return
        widths = self.col_widths(W - 1)
        hh = sc(36)
        bh = self.body_height()
        H = hh + bh + 3
        if int(self.cget("height")) != H:
            self.configure(height=H)
        self.boxes = []
        x = 0
        for d, w in zip(DAYS, widths):
            x2 = x + w
            # header cell: bg-muted, font-semibold, text-muted-foreground, border
            self.create_rectangle(x, 0, x2, hh + 1, fill=C["muted"], outline=C["border"])
            self.create_text((x + x2) / 2, hh / 2 + 1, text=d, font=F(14, "semibold"), fill=C["muted_fg"])
            self.create_rectangle(x, hh + 1, x2, hh + 2 + bh, fill=C["card"], outline=C["border"])
            ey = hh + 2 + sc(8)
            if not self.grouped[d]:
                self.create_text(x + sc(8) + 1, ey + sc(8), anchor="w", text="—", font=F(12), fill=C["muted_fg"])
            for e in self.grouped[d]:
                bx1, bx2 = x + sc(8) + 1, x2 - sc(8)
                gfx.draw_box(self, bx1, ey, bx2, ey + sc(ENTRY_H), sc(R_LG), alpha(C["primary"], 0.05, C["card"]))
                self.create_text(bx1 + sc(8), ey + sc(6 + 8), anchor="w", text=e["subject"], font=F(12, "medium"),
                                 fill=C["card_fg"])
                self.create_text(bx1 + sc(8), ey + sc(6 + 16 + 9), anchor="w", text=e["timeSlot"], font=F(11),
                                 fill=C["muted_fg"])
                if self.hover and self.hover[0] == e["id"]:
                    col = C["destructive"] if self.hover[1] else C["muted_fg"]
                    self.create_image(bx2 - sc(4), ey + sc(4), anchor="ne", image=gfx.icon("trash-2", sc(12), col))
                self.boxes.append((bx1, ey, bx2, ey + sc(ENTRY_H), e))
                ey += sc(ENTRY_H + ENTRY_GAP)
            x = x2

    def _hit(self, ex, ey):
        for x1, y1, x2, y2, e in self.boxes:
            if x1 <= ex <= x2 and y1 <= ey <= y2:
                on_trash = x2 - sc(4) - sc(12) - 2 <= ex <= x2 - sc(2) and y1 + sc(2) <= ey <= y1 + sc(18)
                return e, on_trash
        return None, False

    def _set_hover(self, h):
        if h != self.hover:
            self.hover = h
            self.configure(cursor="hand2" if h and h[1] else "")
            self.draw()

    def _motion(self, ev):
        e, t = self._hit(ev.x, ev.y)
        self._set_hover((e["id"], t) if e else None)

    def _click(self, ev):
        e, t = self._hit(ev.x, ev.y)
        if e and t:
            self.section.delete(e)


class TimetableSection(tk.Frame):
    def __init__(self, parent, dash):
        super().__init__(parent, bg=C["background"])
        self.dash = dash
        bg = C["background"]
        head = tk.Frame(self, bg=bg)
        head.pack(fill="x", padx=sc(8))
        Button(head, "Add Class", self.open_dialog, size="sm", icon="plus", icon_gap=12, bg=bg).pack(side="right")
        SectionHeader(head, "calendar-days", "Class Timetable").pack(side="left", fill="x", expand=True)
        self.empty = tk.Label(self, text="No classes added yet", font=F(14), fg=C["muted_fg"], bg=bg)
        self.table = TimetableTable(self, self)

    def render(self, entries):
        self.empty.pack_forget()
        self.table.pack_forget()
        if not entries:
            self.empty.pack(pady=sc(24 + 16))
        else:
            self.table.pack(fill="x", padx=sc(8), pady=(sc(16), 0))
            self.table.set_entries(entries)

    def delete(self, entry):
        store.delete_timetable_entry(entry["userId"], entry["id"])
        self.dash.load_all()

    def open_dialog(self):
        ClassDialog(self.dash.app, self.dash)


class ClassDialog(Dialog):
    def __init__(self, app, dash):
        super().__init__(app, "Add Class", width=384)
        self.dash = dash
        b, bg, P = self.body, C["background"], sc(4)
        FieldLabel(b, "Day", bg).pack(fill="x", padx=P)
        self.day = Select(b, [(d, d) for d in DAYS], "Mon", bg=bg)
        self.day.pack(fill="x", pady=(P, 0))
        FieldLabel(b, "Time Slot", bg).pack(fill="x", padx=P, pady=(sc(12), 0))
        self.slot = Input(b, placeholder="e.g. 9:00 AM - 10:00 AM", bg=bg, on_enter=self.submit)
        self.slot.pack(fill="x", pady=(P, 0))
        FieldLabel(b, "Subject", bg).pack(fill="x", padx=P, pady=(sc(12), 0))
        self.subject = Input(b, placeholder="e.g. Physics", bg=bg, on_enter=self.submit)
        self.subject.pack(fill="x", pady=(P, 0))
        btns = tk.Frame(b, bg=bg)
        btns.pack(fill="x", padx=P, pady=(sc(12), 0))
        Button(btns, "Add", self.submit, variant="gradient", bg=bg).pack(side="right")
        Button(btns, "Cancel", self.close, variant="outline", bg=bg).pack(side="right", padx=(0, sc(8)))
        self.show()

    def submit(self):
        slot, subject = self.slot.get().strip(), self.subject.get().strip()
        if not slot or not subject:
            return
        store.add_timetable_entry(self.dash.user["id"], self.day.value, slot, subject)
        self.close()
        self.dash.load_all()
