"""TaskCard.tsx: one assignment with badges, progress, a subtask checklist and actions."""
import math
import time
import tkinter as tk

from .. import gfx, store
from ..theme import C, F, sc, mix, alpha
from ..widgets import (Input, CvButton, draw_badge, badge_size, draw_progress, draw_checkbox, wrap_lines,
                       HoverWatch)
from .cards import CardCanvas

ROW, GAP, MAXH = 24, 6, 160            # subtask row (text-sm + py-0.5), space-y-1.5, max-h-40

PRIORITY = {"High": "high", "Medium": "medium", "Low": "low"}


class SubtaskList(tk.Canvas):
    """The checklist (max-h-40 overflow-y-auto). Hovering a row shows the edit / delete icons."""

    def __init__(self, card):
        self.card = card
        super().__init__(card, bg=card.c(C["card"]), highlightthickness=0, bd=0, height=10, width=10)
        self.subs = []
        self.hover_row = None
        self.hover_icon = None
        self.offset = 0
        self.editing = None             # (subtask id, Input, window id)
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: self._set_hover(None, None))
        self.bind("<ButtonRelease-1>", self._click)
        self.bind("<Configure>", lambda e: self.draw())

    def total_height(self):
        n = len(self.subs)
        return sc(n * ROW + max(0, n - 1) * GAP)

    def can_scroll(self):
        return self.total_height() > sc(MAXH)

    def scroll(self, units):
        if not self.can_scroll():
            return False
        self.offset = max(0, min(self.total_height() - self.winfo_height(), self.offset + units * sc(20)))
        self.draw()
        return True

    def _row_at(self, y):
        y += self.offset
        i = int(y // sc(ROW + GAP))
        if 0 <= i < len(self.subs) and y - i * sc(ROW + GAP) < sc(ROW):
            return i
        return None

    def _icon_at(self, x):
        W = self.winfo_width()
        if W - sc(4) - sc(12) - 1 <= x <= W - sc(2):
            return "trash"
        if W - sc(4) - sc(28) - 1 <= x <= W - sc(4) - sc(14):
            return "pencil"
        if sc(2) <= x <= sc(4 + 16 + 2):
            return "check"
        return None

    def _set_hover(self, row, icon):
        if (row, icon) != (self.hover_row, self.hover_icon):
            self.hover_row, self.hover_icon = row, icon
            self.configure(cursor="hand2" if icon else "")
            self.draw()

    def _motion(self, e):
        r = self._row_at(e.y)
        self._set_hover(r, self._icon_at(e.x) if r is not None else None)

    def _click(self, e):
        r = self._row_at(e.y)
        if r is None:
            return
        sub = self.subs[r]
        what = self._icon_at(e.x)
        if self.editing and self.editing[0] == sub["id"]:
            return
        if what == "check":
            self.card.toggle_sub(sub["id"])
        elif what == "pencil":
            self.start_edit(sub)
        elif what == "trash":
            self.card.delete_sub(sub["id"])

    # inline rename ------------------------------------------------------------------
    def start_edit(self, sub):
        self.stop_edit(save=False)
        c = self.card.c
        inp = Input(self, height=24, text_px=14, padx=4, bg=c(C["card"]), tint=c, value=sub["name"],
                    on_enter=lambda: self.stop_edit(True), on_escape=lambda: self.stop_edit(False),
                    on_blur=lambda: self.after(1, lambda: self.stop_edit(True)))
        win = self.create_window(0, 0, window=inp, anchor="nw")
        self.editing = (sub["id"], inp, win)
        self.draw()
        inp.focus()

    def stop_edit(self, save):
        if not self.editing:
            return
        sid, inp, win = self.editing
        self.editing = None
        name = inp.get().strip()
        self.delete(win)
        inp.destroy()
        if save and name:
            self.card.rename_sub(sid, name)
        else:
            self.draw()

    def draw(self):
        keep = self.editing[2] if self.editing else None
        for item in self.find_all():                 # keep the inline-edit entry window
            if item != keep:
                self.delete(item)
        W = self.winfo_width()
        if W < 20:
            return
        c = self.card.c
        self.configure(bg=c(C["card"]))
        for i, sub in enumerate(self.subs):
            y = i * sc(ROW + GAP) - self.offset
            if y > self.winfo_height() or y + sc(ROW) < 0:
                continue
            hov = i == self.hover_row
            if hov:                                    # hover:bg-muted/50 rounded
                gfx.draw_box(self, 0, y, W, y + sc(ROW), sc(4), c(alpha(C["muted"], 0.5, C["card"])))
            draw_checkbox(self, sc(4), y + sc(4), sub["completed"], tint=c)
            editing = self.editing and self.editing[0] == sub["id"]
            if editing:
                self.coords(self.editing[2], sc(4 + 16 + 8) - self.editing[1].m, y - self.editing[1].m)
                self.itemconfigure(self.editing[2], width=W - sc(4 + 16 + 8 + 4 + 28) + 2 * self.editing[1].m)
            else:
                done = sub["completed"]
                self.create_text(sc(28), y + sc(ROW) // 2, anchor="w", font=F(14, strike=done),
                                 text=sub["name"], fill=c(C["muted_fg"] if done else C["card_fg"]))
            if hov:
                for name, x, hc in (("pencil", W - sc(4 + 12 + 4 + 12), C["primary"]),
                                    ("trash-2", W - sc(4 + 12), C["destructive"])):
                    key = "pencil" if name == "pencil" else "trash"
                    col = hc if self.hover_icon == key else C["muted_fg"]
                    self.create_image(x, y + sc(ROW) // 2, anchor="w", image=gfx.icon(name, sc(12), c(col)))
        if self.can_scroll():
            H = self.winfo_height()
            th = max(sc(16), H * H // self.total_height())
            ty = self.offset * (H - th) // max(1, self.total_height() - H)
            gfx.draw_box(self, W - sc(5), ty, W - sc(1), ty + th, sc(2), c(mix(C["card"], "#000000", 0.25)))
        if self.editing:
            self.tag_raise(self.editing[2])


class TaskCard(CardCanvas):
    def __init__(self, parent, dash, task):
        self.dash = dash
        super().__init__(parent, lift=4, fade=0.7 if task["status"] == "completed" else 1.0)
        self.task = task
        self.subs = store.get_subtasks(task["id"])
        self.sublist = SubtaskList(self)
        self.sublist.subs = self.subs
        self.sub_win = self.create_window(0, 0, window=self.sublist, anchor="nw", state="hidden")
        self.add_input = None
        self.add_win = None
        self._make_inputs()
        c = self.c
        mf = C["muted_fg"]
        self.btn_plus = CvButton(self, icon="plus", command=self.add_sub, variant="ghost", height=28, padx=8,
                                 icon_size=14, fg=C["foreground"], tint=c)
        self.btn_done = CvButton(self, "Undo" if task["status"] == "completed" else "Complete", "check",
                                 lambda: dash.toggle_complete(self.task), fg=mf, hover_fg=C["low"], tint=c)
        self.btn_edit = CvButton(self, "Edit", "pencil", lambda: dash.edit_task(self.task), fg=mf,
                                 hover_fg=C["primary"], tint=c)
        self.btn_del = CvButton(self, "Delete", "trash-2", lambda: dash.delete_task(self.task), fg=mf,
                                hover_fg=C["destructive"], tint=c)
        self._pulse_job = None
        self._start_pulse()

    def _make_inputs(self):
        c = self.c
        self.add_input = Input(self, placeholder="+ Add subtask", height=28, text_px=14, bg=c(C["card"]), tint=c,
                               on_enter=self.add_sub)
        self.add_win = self.create_window(0, 0, window=self.add_input, anchor="nw")

    # data ---------------------------------------------------------------------------
    def set_task(self, task):
        """Called after the dashboard reloads; keeps typed text like React keeps component state."""
        was_done = self.task["status"] == "completed"
        self.task = task
        self.subs = store.get_subtasks(task["id"])
        self.sublist.subs = self.subs
        self.btn_done.text = "Undo" if task["status"] == "completed" else "Complete"
        fade = 0.7 if task["status"] == "completed" else 1.0
        if fade != self.fade:
            self.fade = fade
            typed = self.add_input.get()
            self.delete(self.add_win)
            self.add_input.destroy()
            self._make_inputs()
            if typed:
                self.add_input.set(typed)
        self._req_h = None
        self._on_cfg(None)
        self._start_pulse()
        return was_done

    def days(self):
        return store.calc_days_left(self.task["deadline"])

    def urgent(self):
        return self.days() <= 2 and self.task["status"] == "pending"

    def due_today(self):
        return self.days() == 0 and self.task["status"] == "pending"

    # subtask actions (same order of calls as TaskCard.tsx) ------------------------------
    def toggle_sub(self, sid):
        store.toggle_subtask(self.task["id"], sid)
        store.recalc_progress(self.task["userId"], self.task["id"])
        self.dash.load_all()

    def add_sub(self):
        name = self.add_input.get().strip()
        if not name:
            return
        store.add_subtask(self.task["id"], name)
        self.add_input.set("")
        self.add_input.focus()
        store.recalc_progress(self.task["userId"], self.task["id"])
        self.dash.load_all()

    def delete_sub(self, sid):
        store.delete_subtask(self.task["id"], sid)
        store.recalc_progress(self.task["userId"], self.task["id"])
        self.dash.load_all()

    def rename_sub(self, sid, name):
        store.update_subtask_name(self.task["id"], sid, name)
        self.subs = store.get_subtasks(self.task["id"])
        self.sublist.subs = self.subs
        self.sublist.draw()

    # layout -------------------------------------------------------------------------
    def inner_w(self, width):
        return width - 2 - sc(40)

    def content_height(self, width):
        iw = self.inner_w(width)
        n_title = len(wrap_lines(self.task["title"], F(16, "semibold"), iw))
        n_subj = len(wrap_lines(self.task["subject"], F(14), iw))
        h = 1 + 20 + 22 + 12
        h_px = sc(h) + n_title * sc(24) + sc(4) + n_subj * sc(20) + sc(4 + 16 + 8 + 20 + 12 + 28 + 12)
        if self.subs:
            h_px += min(self.sublist.total_height(), sc(MAXH)) + sc(12)
        h_px += sc(28 + 12 + 1 + 12 + 36 + 20 + 1)
        return h_px

    def border_color(self):
        return alpha(C["high"], 0.4, C["card"]) if self.urgent() else C["border"]

    def ring_color(self):
        return alpha(C["high"], 0.2, C["background"]) if self.urgent() else None

    def _badges(self):
        t = self.task
        p = C[PRIORITY[t["priority"]]]
        out = [(t["priority"], p, alpha(p, 0.1, C["card"]), alpha(p, 0.3, C["card"]), None),
               (t["type"], C["foreground"], C["card"], C["border"], "monitor" if t["type"] == "Online" else "file-text")]
        if self.due_today():
            out.append(("Due Today", C["primary_fg"], C["high"], C["high"], "triangle-alert"))
        elif self.urgent():
            out.append(("Urgent", C["high"], C["card"], alpha(C["high"], 0.4, C["card"]), "clock"))
        if t["status"] == "completed":
            out.append(("✓ Done", C["low"], alpha(C["low"], 0.2, C["card"]), alpha(C["low"], 0.3, C["card"]), None))
        return out

    def _start_pulse(self):
        if self.due_today() and self._pulse_job is None:
            self._pulse_job = self.after(80, self._pulse)

    def _pulse(self):
        self._pulse_job = None
        if not self.winfo_exists() or not self.due_today():
            return
        self._draw_badges()
        self._pulse_job = self.after(80, self._pulse)

    def _draw_badges(self):
        self.delete("badge")
        if not hasattr(self, "_bx"):
            return
        x, y = self._bx, self._by
        c = self.c
        for text, fg, fill, border, icon in self._badges():
            if text == "Due Today":          # animate-pulse: opacity 1 -> 0.5 -> 1 every 2 s
                a = 0.75 + 0.25 * math.cos(time.time() * math.pi)
                fg, fill, border = (mix(C["card"], fg, a), mix(C["card"], fill, a), mix(C["card"], border, a))
            w = draw_badge(self, x, y, text, c(fg), c(fill), c(border), icon, tags=("d", "badge"))
            x += w + sc(8)

    def draw_content(self, x1, y1, x2, y2):
        c = self.c
        t = self.task
        X1, X2 = x1 + sc(20), x2 - sc(20)
        iw = X2 - X1
        y = y1 + sc(20)
        self._bx, self._by = X1, y
        self._draw_badges()
        y += sc(22 + 12)
        done = t["status"] == "completed"
        for line in wrap_lines(t["title"], F(16, "semibold"), iw):
            self.create_text(X1, y + sc(12), anchor="w", text=line, font=F(16, "semibold", strike=done),
                             fill=c(C["card_fg"]), tags="d")
            y += sc(24)
        y += sc(4)
        for line in wrap_lines(t["subject"], F(14), iw):
            self.create_text(X1, y + sc(10), anchor="w", text=line, font=F(14), fill=c(C["muted_fg"]), tags="d")
            y += sc(20)
        y += sc(4)
        self.create_text(X1, y + sc(8), anchor="w", text="Deadline: %s" % store.us_date(t["deadline"]), font=F(12),
                         fill=c(C["muted_fg"]), tags="d")
        y += sc(16 + 8)
        d = self.days()
        col = C["high"] if d <= 2 else (C["medium"] if d <= 5 else C["muted_fg"])
        self.create_text(X1, y + sc(10), anchor="w", text=store.days_left_label(t["deadline"]), font=F(14, "medium"),
                         fill=c(col), tags="d")
        y += sc(20 + 12)
        self.create_text(X1, y + sc(8), anchor="w", text="Progress", font=F(12), fill=c(C["muted_fg"]), tags="d")
        self.create_text(X2, y + sc(8), anchor="e", text="%d%%" % t["progress"], font=F(12, "semibold"),
                         fill=c(C["card_fg"]), tags="d")
        y += sc(16 + 4)
        draw_progress(self, X1, y, X2, sc(8), t["progress"], track=c(C["secondary"]), bar=c(C["primary"]), tags="d")
        y += sc(8 + 12)
        if self.subs:
            h = min(self.sublist.total_height(), sc(MAXH))
            self.itemconfigure(self.sub_win, state="normal", width=iw, height=h)
            self.coords(self.sub_win, X1, y)
            self.sublist.configure(bg=c(C["card"]))
            self.sublist.draw()
            y += h + sc(12)
        else:
            self.itemconfigure(self.sub_win, state="hidden")
        # + Add subtask  [input flex-1][gap-1][ghost h-7 px-2]
        m = self.add_input.m
        bw = self.btn_plus.w
        self.coords(self.add_win, X1 - m, y - m)
        self.itemconfigure(self.add_win, width=iw - bw - sc(4) + 2 * m)
        self.btn_plus.place(X2 - bw, y)
        y += sc(28 + 12)
        self.create_rectangle(X1, y, X2, y + 1, fill=c(C["border"]), outline="", tags="d")   # border-t
        y += 1 + sc(12)
        x = X1
        for b in (self.btn_done, self.btn_edit, self.btn_del):
            tw = b.font.measure(b.text)
            b.w = b.padx * 2 + tw + b.isz + b.gap
            b.place(x, y)
            x += b.w + sc(8)
