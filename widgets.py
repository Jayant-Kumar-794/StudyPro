"""tkinter versions of the shadcn/ui components used by the web app.

Button, Input, Select, DateButton/DatePicker, DateInput, Checkbox, Badge, ProgressBar, Tabs,
ScrollArea, Dialog and Toast. Sizes are CSS pixels (scaled with sc()) taken from the
Tailwind classes of the original components.
"""
import calendar
import datetime as dt
import sys
import tkinter as tk

from . import gfx
from .theme import C, F, sc, mix, alpha, R_MD, R_SM, R_LG, ellipsize

IS_WIN = sys.platform == "win32"


def wrap_lines(text, font, width):
    """Split text into lines that fit width (CSS normal wrapping)."""
    out = []
    for para in str(text).split("\n"):
        words, line = para.split(" "), ""
        for w in words:
            t = (line + " " + w) if line else w
            if font.measure(t) <= width or not line:
                line = t
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


def wheel_units(event):
    if getattr(event, "num", None) == 4:
        return -1
    if getattr(event, "num", None) == 5:
        return 1
    return -1 if event.delta > 0 else 1


# =========================================================================== Button
class Button(tk.Canvas):
    """shadcn <Button>.  variant: gradient | outline | ghost ; size: default (h-10 px-4) | sm (h-9 px-3)

    icon_gap: space between icon and text (gap-2 + mr-1 = 12, gap-2 + mr-2 = 16).
    hover_fg: text colour on hover (e.g. hover:text-priority-low) - ghost buttons get bg-accent on hover.
    """

    def __init__(self, parent, text="", command=None, variant="gradient", size="default", icon=None,
                 icon_gap=16, width=None, fg=None, hover_fg=None, bg=None, icon_only=False, font=None):
        self.bgc = bg or parent.cget("bg")
        self.h = sc(40 if size == "default" else (28 if size == "xs" else 36))
        self.padx = sc(16 if size == "default" else (8 if size == "xs" else 12))
        self.text, self.command, self.variant, self.icon = text, command, variant, icon
        self.icon_gap = sc(icon_gap if text else 0)
        self.fg = fg or (C["primary_fg"] if variant == "gradient" else C["foreground"])
        self.hover_fg = hover_fg
        self.font = font or F(14, "medium")
        self.isz = sc(16 if size != "xs" else 14)
        self.hover = False
        self.disabled = False
        self.fixed_w = width
        tw = self.font.measure(text) if text else 0
        self.w = width or (self.padx * 2 + tw + (self.isz + self.icon_gap if icon else 0))
        super().__init__(parent, width=self.w, height=self.h, bg=self.bgc, highlightthickness=0, bd=0,
                         cursor="hand2")
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", self._click)
        self.bind("<Configure>", lambda e: self.draw())
        self.draw()

    def _set_hover(self, v):
        self.hover = v
        self.draw()

    def set_disabled(self, v):
        self.disabled = v
        self.configure(cursor="arrow" if v else "hand2")
        self.draw()

    def set_text(self, text):
        self.text = text
        self.draw()

    def _click(self, e):
        if self.disabled:
            return
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height() and self.command:
            self.command()

    def draw(self):
        self.delete("all")
        W = self.winfo_width()
        if W <= 2:
            W = self.w
        H = self.h
        fg = self.fg
        hov = self.hover and not self.disabled
        if self.variant == "gradient":
            self.create_image(0, 0, anchor="nw", image=gfx.gradient_box(W, H, sc(R_MD), C["primary"], C["accent"],
                                                                         0.9 if hov else 1.0))
        elif self.variant == "outline":
            fill = C["accent"] if hov else C["background"]
            gfx.draw_box(self, 0, 0, W, H, sc(R_MD), fill, C["input"] if not hov else C["accent"])
            if hov:
                fg = self.hover_fg or C["accent_fg"]
        elif self.variant == "ghost":
            if hov:
                gfx.draw_box(self, 0, 0, W, H, sc(R_MD), C["accent"])
                fg = self.hover_fg or C["accent_fg"]
        if self.disabled:
            fg = mix(self.bgc, fg, 0.5)
        tw = self.font.measure(self.text) if self.text else 0
        total = tw + (self.isz + self.icon_gap if self.icon else 0)
        x = (W - total) / 2.0
        if self.icon:
            self.create_image(int(x), H // 2, anchor="w", image=gfx.icon(self.icon, self.isz, fg))
            x += self.isz + self.icon_gap
        if self.text:
            self.create_text(int(x), H // 2, anchor="w", text=self.text, fill=fg, font=self.font)


# =========================================================================== Input
class Input(tk.Canvas):
    """shadcn <Input>: h-10 rounded-md border border-input bg-background px-3 text-sm, focus ring-2 ring-offset-2.

    The canvas has an extra margin M around the field so the focus ring can be drawn outside it
    (like a CSS box-shadow) without changing the layout.
    """
    M = 4

    def __init__(self, parent, placeholder="", password=False, height=40, text_px=14, padx=12, icon=None,
                 bg=None, field_bg=None, on_enter=None, on_change=None, on_escape=None, on_blur=None, width=None,
                 ring=True, value="", tint=None):
        self.t = tint or (lambda c: c)
        self.bgc = bg or parent.cget("bg")
        self.m = sc(self.M)
        self.h = sc(height)
        self.field_bg = field_bg or self.t(C["background"])
        self.placeholder = placeholder
        self.password = password
        self.icon = icon
        self.ring = ring
        self.focused = False
        self.font = F(text_px)
        super().__init__(parent, height=self.h + 2 * self.m, bg=self.bgc, highlightthickness=0, bd=0,
                         width=(sc(width) + 2 * self.m) if width else 100, cursor="xterm")
        self.var = tk.StringVar(value=value)
        self.entry = tk.Entry(self, textvariable=self.var, bd=0, relief="flat", highlightthickness=0,
                              bg=self.field_bg, fg=self.t(C["foreground"]), insertbackground=C["foreground"],
                              font=self.font, disabledbackground=self.field_bg,
                              selectbackground=alpha(C["primary"], 0.25, "#ffffff"), selectforeground=C["foreground"])
        self.padl = sc(36 if icon else padx)
        self.padr = sc(padx)
        self.win = self.create_window(self.m + self.padl, self.m + self.h // 2, window=self.entry, anchor="w")
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<KeyPress>", self._key)
        self.entry.bind("<<Paste>>", lambda e: self._clear_ph(), add="+")
        self.entry.bind("<ButtonRelease-1>", self._ph_click, add="+")
        self.entry.bind("<B1-Motion>", lambda e: "break" if self._ph_shown else None)
        self.entry.bind("<FocusOut>", self._focus_out)
        if on_enter:
            self.entry.bind("<Return>", lambda e: (on_enter(), "break")[1])
        if on_escape:
            self.entry.bind("<Escape>", lambda e: (on_escape(), "break")[1])
        self._on_blur = on_blur
        self._last = value
        if on_change:
            def changed(*a):
                v = self.get()
                if v != self._last:
                    self._last = v
                    on_change(v)
            self.var.trace_add("write", changed)
        self.bind("<Button-1>", lambda e: self.focus())
        self.entry.bind("<Button-1>", lambda e: self._grab_focus(), add="+")
        self.bind("<Configure>", lambda e: self.draw())
        self._ph_shown = False
        self._show_placeholder()
        self.draw()

    # placeholder handling ---------------------------------------------------
    def _show_placeholder(self):
        if not self.var.get() and self.placeholder:
            self._ph_shown = True
            self.entry.configure(show="", fg=self.t(C["muted_fg"]))
            self.var.set(self.placeholder)
        elif self.password and self.var.get():
            self.entry.configure(show="•")

    def _focus_in(self, e):
        self.focused = True
        if self._ph_shown:
            self.entry.icursor(0)
        self.draw()

    def _clear_ph(self):
        if self._ph_shown:
            self._ph_shown = False
            self.var.set("")
            self.entry.configure(fg=self.t(C["foreground"]), show="•" if self.password else "")

    def _key(self, e):
        if not self._ph_shown:
            return None
        if e.keysym in ("BackSpace", "Delete", "Left", "Right", "Home", "End"):
            return "break"
        if e.char and e.char.isprintable():
            self._clear_ph()                 # the typed character is inserted by the normal binding
        return None

    def _ph_click(self, e):
        if self._ph_shown:
            self.entry.after(1, lambda: (self.entry.icursor(0), self.entry.selection_clear()))

    def _focus_out(self, e):
        self.focused = False
        self._show_placeholder()
        self.draw()
        if self._on_blur:
            self._on_blur()

    def get(self):
        return "" if self._ph_shown else self.var.get()

    def set(self, value):
        if self._ph_shown:
            self._ph_shown = False
            self.entry.configure(fg=self.t(C["foreground"]), show="•" if self.password else "")
        self.var.set(value)
        if not value:
            self._show_placeholder()
        elif self.password:
            self.entry.configure(show="•")

    def _grab_focus(self):
        """Borderless windows (dialogs) do not always get keyboard focus from a click."""
        if self.focus_get() is not self.entry:
            try:
                self.entry.focus_force() if IS_WIN else self.entry.focus_set()
            except tk.TclError:
                pass

    def focus(self):
        self.entry.focus_set()
        self._grab_focus()
        self.entry.icursor(0 if self._ph_shown else "end")

    def draw(self):
        self.delete("deco")
        W, m, H = self.winfo_width(), self.m, self.h
        if W < 10:
            return
        if self.focused and self.ring:            # ring-2 ring-ring ring-offset-2
            gfx.draw_box(self, m - sc(4), m - sc(4), W - m + sc(4), m + H + sc(4), sc(R_MD) + sc(4), C["ring"],
                         tags="deco")
            gfx.draw_box(self, m - sc(2), m - sc(2), W - m + sc(2), m + H + sc(2), sc(R_MD) + sc(2), self.bgc,
                         tags="deco")
        gfx.draw_box(self, m, m, W - m, m + H, sc(R_MD), self.field_bg, self.t(C["input"]), tags="deco")
        if self.icon:
            self.create_image(m + sc(12), m + H // 2, anchor="w", image=gfx.icon(self.icon, sc(16), self.t(C["muted_fg"])),
                              tags="deco")
        self.itemconfigure(self.win, width=max(10, W - 2 * m - self.padl - self.padr))
        self.tag_lower("deco")


# =========================================================================== Popup (base for dropdowns)
class Popup(tk.Toplevel):
    """Borderless floating panel (select list, date picker). Closes on outside click or Escape."""
    opened = []

    def __init__(self, anchor, width, height, on_close=None, bg_under=None):
        root = anchor.winfo_toplevel()
        super().__init__(root)
        self.withdraw()
        self.overrideredirect(True)
        self.on_close = on_close
        self.cv = tk.Canvas(self, width=width, height=height, highlightthickness=0, bd=0,
                            bg=bg_under or C["background"])
        self.cv.pack()
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + sc(4)
        self.geometry("%dx%d+%d+%d" % (width, height, x, y))
        if IS_WIN:
            try:
                self.attributes("-transparentcolor", "#ff00fe")
                self.cv.configure(bg="#ff00fe")
            except tk.TclError:
                pass
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.bind("<Escape>", lambda e: self.close())
        self._rootw = root
        self._bid = root.bind("<Button-1>", self._outside, add="+")
        try:
            self.focus_set()
        except tk.TclError:
            pass
        Popup.opened.append(self)
        self.after(50, self._grab)

    def _grab(self):
        try:
            self.grab_set()
            self.bind("<Button-1>", self._maybe_outside)
        except tk.TclError:
            pass

    def _maybe_outside(self, e):
        x, y = e.x_root - self.winfo_rootx(), e.y_root - self.winfo_rooty()
        if not (0 <= x < self.winfo_width() and 0 <= y < self.winfo_height()):
            self.close()

    def _outside(self, e):
        self.close()

    def close(self):
        if getattr(self, "_closed", False):
            return
        self._closed = True
        if self in Popup.opened:
            Popup.opened.remove(self)
        try:
            self._rootw.unbind("<Button-1>", self._bid)
        except Exception:
            pass
        try:
            self.grab_release()
        except tk.TclError:
            pass
        try:                                   # hand the focus back before the window disappears
            (Dialog._open[-1].top if Dialog._open else self._rootw).focus_set()
        except tk.TclError:
            pass
        if self.winfo_exists():
            self.destroy()
        if Dialog._open:
            Dialog._open[-1]._grab()
        if self.on_close:
            self.on_close()


# =========================================================================== Select
class Select(tk.Canvas):
    """shadcn <Select>: trigger like an input with a chevron; list with check mark, hover = bg-accent."""
    M = 4

    def __init__(self, parent, options, value=None, on_change=None, width=None, bg=None):
        self.bgc = bg or parent.cget("bg")
        self.options = options               # [(value, label)]
        self.value = value if value is not None else options[0][0]
        self.on_change = on_change
        self.m = sc(self.M)
        self.h = sc(40)
        self.popup = None
        self.font = F(14)
        super().__init__(parent, height=self.h + 2 * self.m, width=(sc(width) + 2 * self.m) if width else 100,
                         bg=self.bgc, highlightthickness=0, bd=0, cursor="hand2")
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<ButtonRelease-1>", lambda e: self.open())
        self.draw()

    def label(self):
        return dict(self.options).get(self.value, "")

    def set(self, value, notify=False):
        self.value = value
        self.draw()
        if notify and self.on_change:
            self.on_change(value)

    def draw(self):
        self.delete("all")
        W, m, H = self.winfo_width(), self.m, self.h
        if W < 10:
            return
        if self.popup is not None:            # focus:ring-2 while open
            gfx.draw_box(self, m - sc(4), m - sc(4), W - m + sc(4), m + H + sc(4), sc(R_MD) + sc(4), C["ring"])
            gfx.draw_box(self, m - sc(2), m - sc(2), W - m + sc(2), m + H + sc(2), sc(R_MD) + sc(2), self.bgc)
        gfx.draw_box(self, m, m, W - m, m + H, sc(R_MD), C["background"], C["input"])
        self.create_text(m + sc(12), m + H // 2, anchor="w",
                         text=ellipsize(self.label(), self.font, W - 2 * m - sc(12 + 8 + 16 + 12)),
                         fill=C["foreground"], font=self.font)
        self.create_image(W - m - sc(12), m + H // 2, anchor="e",
                          image=gfx.icon("chevron-down", sc(16), mix(self.bgc, C["foreground"], 0.5)))

    def open(self):
        if self.popup is not None:
            return
        W = self.winfo_width() - 2 * self.m
        ih = sc(32)
        H = len(self.options) * ih + sc(8) + 2
        anchor = self
        p = Popup(anchor, W, H, on_close=self._closed, bg_under=self.bgc)
        p.geometry("+%d+%d" % (self.winfo_rootx() + self.m, self.winfo_rooty() + self.m + self.h + sc(4)))
        self.popup = p
        self.hover_i = [v for v, _l in self.options].index(self.value)
        self.draw()
        self._draw_list()
        p.cv.bind("<Motion>", self._motion)
        p.cv.bind("<ButtonRelease-1>", self._pick)
        p.bind("<Up>", lambda e: self._key(-1))
        p.bind("<Down>", lambda e: self._key(1))
        p.bind("<Return>", lambda e: self._choose(self.hover_i))

    def _draw_list(self):
        p = self.popup
        cv = p.cv
        cv.delete("all")
        W, H = int(cv.cget("width")), int(cv.cget("height"))
        gfx.draw_box(cv, 0, 0, W, H, sc(R_MD), C["popover"], C["border"])
        ih = sc(32)
        for i, (v, lab) in enumerate(self.options):
            y = sc(4) + 1 + i * ih
            fg = C["foreground"]
            if i == self.hover_i:
                gfx.draw_box(cv, sc(4), y, W - sc(4), y + ih, sc(R_SM), C["accent"])
                fg = C["accent_fg"]
            if v == self.value:
                cv.create_image(sc(4) + sc(8), y + ih // 2, anchor="w", image=gfx.icon("check", sc(16), fg))
            cv.create_text(sc(4) + sc(32), y + ih // 2, anchor="w", text=lab, fill=fg, font=self.font)

    def _index_at(self, y):
        i = int((y - sc(4) - 1) // sc(32))
        return i if 0 <= i < len(self.options) else None

    def _motion(self, e):
        i = self._index_at(e.y)
        if i is not None and i != self.hover_i:
            self.hover_i = i
            self._draw_list()

    def _key(self, d):
        self.hover_i = (self.hover_i + d) % len(self.options)
        self._draw_list()

    def _pick(self, e):
        i = self._index_at(e.y)
        if i is not None:
            self._choose(i)

    def _choose(self, i):
        v = self.options[i][0]
        if self.popup:
            self.popup.close()
        self.set(v, notify=True)

    def _closed(self):
        self.popup = None
        self.draw()


# =========================================================================== Date picker (react-day-picker look)
class DatePicker(Popup):
    """react-day-picker month: Su..Sa, selected day = bg-primary, today = bg-accent, outside days muted.
    Positions measured from the web version (rows are 36 px cells with mt-2 between weeks)."""

    def __init__(self, anchor, selected, on_pick, on_close=None, x=None, y=None):
        self.sel = selected
        self.on_pick = on_pick
        base = selected or dt.date.today()
        self.year, self.month = base.year, base.month
        self.cell = sc(36)
        self.W = self.cell * 7 + sc(12) * 2 + 2
        self.hover = None
        super().__init__(anchor, self.W, self._height(), on_close=on_close)
        if x is not None:
            self.geometry("+%d+%d" % (x, y))
        self.cv.bind("<Motion>", self._motion)
        self.cv.bind("<Leave>", lambda e: self._set_hover(None))
        self.cv.bind("<ButtonRelease-1>", self._click)
        self.draw()

    def _height(self):
        return sc(99) + sc(44) * (len(self._days()) - 1) + sc(18) + sc(13)

    def _days(self):
        first = dt.date(self.year, self.month, 1)
        start = first - dt.timedelta(days=(first.weekday() + 1) % 7)     # weeks start on Sunday
        weeks = []
        d = start
        while True:
            weeks.append([d + dt.timedelta(days=i) for i in range(7)])
            d += dt.timedelta(days=7)
            if d.month != self.month:
                break
        return weeks

    def _cell_box(self, r, c):
        x = sc(13) + c * self.cell
        cy = sc(99) + r * sc(44)
        return x, cy - self.cell // 2

    def _nav_x(self):
        return sc(17), self.W - sc(17) - sc(28)

    def draw(self):
        cv = self.cv
        cv.delete("all")
        W, H = self.W, self._height()
        if int(cv.cget("height")) != H:
            cv.configure(height=H)
            self.geometry("%dx%d" % (W, H))
        gfx.draw_box(cv, 0, 0, W, H, sc(R_MD), C["popover"], C["border"])
        cy = sc(25)
        cv.create_text(W // 2, cy, text=dt.date(self.year, self.month, 1).strftime("%B %Y"),
                       font=F(14, "medium"), fill=C["foreground"])
        for tag, x, ic in zip(("prev", "next"), self._nav_x(), ("chevron-left", "chevron-right")):
            hov = self.hover == tag
            a = 1.0 if hov else 0.5                       # opacity-50 hover:opacity-100
            gfx.draw_box(cv, x, cy - sc(14), x + sc(28), cy + sc(14), sc(R_MD),
                         C["accent"] if hov else C["popover"], C["accent"] if hov else mix(C["popover"], C["input"], a))
            cv.create_image(x + sc(14), cy, image=gfx.icon(ic, sc(16), C["accent_fg"] if hov else
                                                            mix(C["popover"], C["foreground"], a)))
        for i, n in enumerate(["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]):
            cv.create_text(sc(13) + i * self.cell + self.cell // 2, sc(62), text=n, font=F(13), fill=C["muted_fg"])
        today = dt.date.today()
        for r, week in enumerate(self._days()):
            for c, d in enumerate(week):
                x, y = self._cell_box(r, c)
                outside = d.month != self.month
                fg = C["foreground"]
                if d == self.sel and not outside:
                    gfx.draw_box(cv, x, y, x + self.cell, y + self.cell, sc(R_MD), C["primary"])
                    fg = C["primary_fg"]
                elif (d == today or self.hover == d) and not outside:
                    gfx.draw_box(cv, x, y, x + self.cell, y + self.cell, sc(R_MD), C["accent"])
                    fg = C["accent_fg"]
                elif outside:
                    fg = mix(C["popover"], C["muted_fg"], 0.5)
                cv.create_text(x + self.cell // 2, y + self.cell // 2, text=str(d.day), font=F(14), fill=fg)

    def _hit(self, e):
        cy = sc(25)
        if cy - sc(14) <= e.y <= cy + sc(14):
            px, nx = self._nav_x()
            if px <= e.x <= px + sc(28):
                return "prev"
            if nx <= e.x <= nx + sc(28):
                return "next"
        for r, week in enumerate(self._days()):
            for c, d in enumerate(week):
                x, y = self._cell_box(r, c)
                if x <= e.x < x + self.cell and y <= e.y < y + self.cell:
                    return d
        return None

    def _set_hover(self, h):
        if h != self.hover:
            self.hover = h
            self.draw()

    def _motion(self, e):
        self._set_hover(self._hit(e))

    def _click(self, e):
        h = self._hit(e)
        if h == "prev":
            self.month -= 1
            if self.month == 0:
                self.month, self.year = 12, self.year - 1
        elif h == "next":
            self.month += 1
            if self.month == 13:
                self.month, self.year = 1, self.year + 1
        elif isinstance(h, dt.date) and h.month == self.month:
            self.sel = h
            self.on_pick(h)                 # like the web: the popover stays open
        self.draw()


def ordinal(n):
    return "%d%s" % (n, "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


def format_ppp(d):
    """date-fns format(date, 'PPP') -> 'November 20th, 2026'."""
    return "%s %s, %d" % (d.strftime("%B"), ordinal(d.day), d.year)


class DateButton(Button):
    """Outline button 'Pick a date' that opens the DatePicker (TaskDialog deadline field)."""

    def __init__(self, parent, value=None, bg=None):
        self.value = value
        self.picker = None
        super().__init__(parent, "", self._open, variant="outline", icon="calendar", icon_gap=16, bg=bg)

    def draw(self):
        self.delete("all")
        W, H = max(self.winfo_width(), 10), self.h
        hov = self.hover or self.picker is not None
        fill = C["accent"] if hov else C["background"]
        gfx.draw_box(self, 0, 0, W, H, sc(R_MD), fill, C["accent"] if hov else C["input"])
        if hov:
            fg = C["accent_fg"]
        else:
            fg = C["foreground"] if self.value else C["muted_fg"]
        x = sc(16)
        self.create_image(x, H // 2, anchor="w", image=gfx.icon("calendar", sc(16), fg))
        text = format_ppp(self.value) if self.value else "Pick a date"
        self.create_text(x + sc(32), H // 2, anchor="w", text=ellipsize(text, F(14), W - x - sc(40)), fill=fg,
                         font=F(14))

    def _open(self):
        if self.picker is not None:
            return
        self.picker = DatePicker(self, self.value, self._picked, on_close=self._closed,
                                 x=self.winfo_rootx(), y=self.winfo_rooty() + self.h + sc(4))
        self.draw()

    def _picked(self, d):
        self.value = d
        self.draw()

    def _closed(self):
        self.picker = None
        self.draw()


class DateInput(Input):
    """<Input type="date">: shows mm/dd/yyyy, accepts typing and has a calendar icon on the right."""

    def __init__(self, parent, bg=None):
        super().__init__(parent, placeholder="mm/dd/yyyy", bg=bg)
        self.picker = None
        self.padr = sc(36)
        self.bind("<Button-1>", self._click)
        self.entry.bind("<KeyRelease>", self._format)
        self.draw()

    def draw(self):
        super().draw()
        W = self.winfo_width()
        if W > 10:
            self.create_image(W - self.m - sc(12), self.m + self.h // 2, anchor="e", tags="deco",
                              image=gfx.icon("calendar", sc(16), C["foreground"]))

    def _click(self, e):
        if e.x > self.winfo_width() - self.m - sc(36):
            self._open()
        else:
            self.entry.focus_set()

    def _format(self, e):
        if e.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab"):
            return
        digits = "".join(ch for ch in self.get() if ch.isdigit())[:8]
        out = digits[:2] + ("/" + digits[2:4] if len(digits) > 2 else "") + ("/" + digits[4:] if len(digits) > 4 else "")
        if out != self.get():
            self.set(out)
            self.entry.icursor("end")

    def value(self):
        try:
            return dt.datetime.strptime(self.get(), "%m/%d/%Y").date()
        except ValueError:
            return None

    def _open(self):
        if self.picker is not None:
            return
        self.picker = DatePicker(self, self.value(), self._picked, on_close=self._closed,
                                 x=self.winfo_rootx() + self.m, y=self.winfo_rooty() + self.m + self.h + sc(4))

    def _picked(self, d):
        self.set(d.strftime("%m/%d/%Y"))

    def _closed(self):
        self.picker = None


# =========================================================================== small canvas drawings
def draw_checkbox(cv, x, y, checked, tags=(), tint=None):
    """Radix checkbox h-4 w-4 rounded-sm (radius 8 = a circle here) border-primary; checked = filled + check."""
    t = tint or (lambda c: c)
    d = sc(16)
    if checked:
        cv.create_image(x, y, anchor="nw", image=gfx.circle(d, t(C["primary"])), tags=tags)
        cv.create_image(x + d // 2, y + d // 2, image=gfx.icon("check", d, t(C["primary_fg"])), tags=tags)
    else:
        cv.create_image(x, y, anchor="nw", image=gfx.circle(d, None, t(C["primary"]), 1.0 * sc(1)), tags=tags)


def badge_size(text, icon=None):
    f = F(12, "semibold")
    w = sc(10) * 2 + f.measure(text) + 2 + ((sc(12) + sc(4)) if icon else 0)
    return w, sc(22)


def draw_badge(cv, x, y, text, fg, fill=None, border=None, icon=None, tags=()):
    """Badge: rounded-full border px-2.5 py-0.5 text-xs font-semibold (+ w-3 h-3 mr-1 icon)."""
    w, h = badge_size(text, icon)
    gfx.draw_box(cv, x, y, x + w, y + h, h // 2, fill or cv.cget("bg"), border, tags=tags)
    tx = x + sc(10) + 1
    if icon:
        cv.create_image(tx, y + h // 2, anchor="w", image=gfx.icon(icon, sc(12), fg), tags=tags)
        tx += sc(12) + sc(4)
    cv.create_text(tx, y + h // 2, anchor="w", text=text, fill=fg, font=F(12, "semibold"), tags=tags)
    return w


def draw_progress(cv, x1, y, x2, h, value, track=None, bar=None, tags=()):
    """Radix Progress: rounded-full track bg-secondary, indicator bg-primary (clipped by the track)."""
    track = track or C["secondary"]
    bar = bar or C["primary"]
    r = h // 2
    gfx.draw_box(cv, x1, y, x2, y + h, r, track, tags=tags)
    w = int(round((x2 - x1) * max(0, min(100, value)) / 100.0))
    if w <= 0:
        return
    if w >= h:
        gfx.draw_box(cv, x1, y, x1 + w, y + h, r, bar, tags=tags)
        if w < (x2 - x1) - r:                     # square right edge (translateX inside overflow-hidden)
            cv.create_rectangle(x1 + w - r, y, x1 + w, y + h, fill=bar, outline="", width=0, tags=tags)
    else:
        gfx.draw_box(cv, x1, y, x1 + h, y + h, r, bar, tags=tags)
        cv.create_rectangle(x1 + w, y, x1 + h, y + h, fill=track, outline="", width=0, tags=tags)


# =========================================================================== Tabs
class Tabs(tk.Canvas):
    """TabsList: grid grid-cols-4 h-10 rounded-md bg-muted p-1; active trigger bg-background shadow-sm."""

    def __init__(self, parent, tabs, value, on_change, width=512):
        self.tabs, self.value, self.on_change = tabs, value, on_change
        self.w = sc(width)
        super().__init__(parent, width=self.w, height=sc(40), bg=parent.cget("bg"), highlightthickness=0, bd=0,
                         cursor="hand2")
        self.bind("<ButtonRelease-1>", self._click)
        self.draw()

    def draw(self):
        self.delete("all")
        W, H = self.w, sc(40)
        gfx.draw_box(self, 0, 0, W, H, sc(R_MD), C["muted"])
        n = len(self.tabs)
        tw = (W - sc(8)) / float(n)
        for i, (key, label) in enumerate(self.tabs):
            x1 = sc(4) + i * tw
            if key == self.value:
                gfx.draw_box(self, x1, sc(4) + 1, x1 + tw, H - sc(4) + 1, sc(R_SM), mix(C["muted"], C["black"], 0.04))
                gfx.draw_box(self, x1, sc(4), x1 + tw, H - sc(4), sc(R_SM), C["background"])
                fg = C["foreground"]
            else:
                fg = C["muted_fg"]
            self.create_text(x1 + tw / 2, H / 2, text=label, fill=fg, font=F(14, "medium"))

    def _click(self, e):
        n = len(self.tabs)
        i = int((e.x - sc(4)) // ((self.w - sc(8)) / float(n)))
        if 0 <= i < n and self.tabs[i][0] != self.value:
            self.value = self.tabs[i][0]
            self.draw()
            self.on_change(self.value)


# =========================================================================== ScrollArea
class ScrollArea(tk.Frame):
    """Vertically scrolling page (the browser window scroll). Content goes into .body"""

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.body = tk.Frame(self.canvas, bg=bg)
        self.win = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.bar = tk.Canvas(self, width=sc(10), bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")      # overlay scrollbar
        self.body.bind("<Configure>", lambda e: self._update())
        self.canvas.bind("<Configure>", lambda e: self._update())
        self.bar.bind("<Button-1>", self._bar_click)
        self.bar.bind("<B1-Motion>", self._bar_drag)
        self._drag = None

    def _update(self):
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.itemconfigure(self.win, width=cw)
        bh = self.body.winfo_reqheight()
        self.canvas.configure(scrollregion=(0, 0, cw, max(bh, ch)))
        if bh <= ch:
            self.canvas.yview_moveto(0)
        self._draw_bar()

    def _draw_bar(self):
        self.bar.delete("all")
        f0, f1 = self.canvas.yview()
        if f1 - f0 >= 0.999:
            return
        H = self.bar.winfo_height()
        y0, y1 = int(f0 * H) + sc(2), int(f1 * H) - sc(2)
        gfx.draw_box(self.bar, sc(2), y0, sc(8), max(y0 + sc(20), y1), sc(3), mix(C["background"], "#000000", 0.25))

    def scroll(self, units):
        f0, f1 = self.canvas.yview()
        if f1 - f0 < 0.999:
            self.canvas.yview_scroll(units * 3, "units")
            self._draw_bar()

    def _bar_click(self, e):
        f0, f1 = self.canvas.yview()
        H = self.bar.winfo_height()
        self._drag = (e.y, f0)
        if not (f0 * H <= e.y <= f1 * H):
            self.canvas.yview_moveto(max(0, e.y / float(H) - (f1 - f0) / 2))
            self._drag = (e.y, self.canvas.yview()[0])
        self._draw_bar()

    def _bar_drag(self, e):
        if self._drag:
            y0, f0 = self._drag
            self.canvas.yview_moveto(f0 + (e.y - y0) / float(self.bar.winfo_height()))
            self._draw_bar()

    def to_top(self):
        self.canvas.yview_moveto(0)
        self._draw_bar()


# =========================================================================== Dialog
class Dialog:
    """shadcn <Dialog>: dark overlay (bg-black/80) + centred panel max-w-md p-6 rounded-lg border shadow-lg."""
    _open = []

    def __init__(self, app, title, width=448, on_close=None):
        self.app = app
        root = app.root
        self.on_close = on_close
        self.width = sc(width)
        self.closed = False
        # overlay
        self.overlay = tk.Toplevel(root)
        self.overlay.withdraw()
        self.overlay.overrideredirect(True)
        self.overlay.configure(bg="#000000", cursor="arrow")
        try:
            self.overlay.attributes("-alpha", 0.8)
        except tk.TclError:
            pass
        self.overlay.bind("<Button-1>", lambda e: self.close())
        # panel
        self.top = tk.Toplevel(root)
        self.top.withdraw()
        self.top.overrideredirect(True)
        self.corner_bg = mix("#000000", C["background"], 0.2)       # what shows behind the rounded corners
        self.top.configure(bg=self.corner_bg)
        if IS_WIN:
            try:
                self.top.attributes("-transparentcolor", "#ff00fe")
                self.corner_bg = "#ff00fe"
                self.top.configure(bg=self.corner_bg)
            except tk.TclError:
                pass
        self.cv = tk.Canvas(self.top, bg=self.corner_bg, highlightthickness=0, bd=0, width=self.width)
        self.cv.pack(fill="both", expand=True)
        self.body = tk.Frame(self.cv, bg=C["background"])
        # the body is 4 px wider on each side so inputs can draw their focus ring there
        self.cv.create_window(sc(24) - sc(4), sc(24) + sc(18) + sc(16) + sc(8) - sc(4), window=self.body,
                              anchor="nw", width=self.width - 2 * sc(24) + 2 * sc(4))
        self.title = title
        self.close_hover = False
        self.cv.bind("<Motion>", lambda e: self._ch(self._on_close_btn(e)))
        self.cv.bind("<Leave>", lambda e: self._ch(False))
        self.cv.bind("<ButtonRelease-1>", lambda e: self._on_close_btn(e) and self.close())
        self.top.bind("<Escape>", lambda e: self.close())
        self.body.bind("<Configure>", lambda e: self._layout())
        self._cfg = root.bind("<Configure>", lambda e: self._place(), add="+")

    def _on_close_btn(self, e):
        x = self.width - sc(32)
        return x - sc(4) <= e.x <= x + sc(20) and sc(12) <= e.y <= sc(36)

    def _ch(self, v):
        if v == self.close_hover:
            return
        self.close_hover = v
        self.cv.configure(cursor="hand2" if v else "")
        self._draw()

    def _draw(self):
        cv = self.cv
        cv.delete("frame")
        W, H = self.width, int(cv.cget("height") or 10)
        gfx.draw_box(cv, 0, 0, W, H, sc(R_LG), C["background"], C["border"], tags="frame")
        cv.create_text(sc(24), sc(24) + sc(9), text=self.title, anchor="w", font=F(18, "semibold"),
                       fill=C["foreground"], tags="frame")
        col = C["foreground"] if self.close_hover else mix(C["background"], C["foreground"], 0.7)
        x, y = W - sc(16) - sc(16), sc(16)
        cv.create_rectangle(x - sc(2), y - sc(2), x + sc(18), y + sc(18), fill=C["background"], outline="",
                            tags=("frame", "close"))
        cv.create_image(x, y, anchor="nw", image=gfx.icon("x", sc(16), col), tags=("frame", "close"))
        cv.tag_lower("frame")

    def _layout(self):
        h = sc(24) + sc(18) + sc(16) + sc(8) - sc(4) + self.body.winfo_reqheight() + sc(24)
        self.cv.configure(height=h)
        self._draw()
        self._place()

    def _place(self):
        if self.closed:
            return
        root = self.app.root
        rx, ry, rw, rh = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
        self.overlay.geometry("%dx%d+%d+%d" % (rw, rh, rx, ry))
        self.top.update_idletasks()
        h = self.top.winfo_reqheight()
        self.top.geometry("%dx%d+%d+%d" % (self.width, h, rx + (rw - self.width) // 2, ry + max(0, (rh - h) // 2)))

    def show(self, focus=None):
        self.body.update_idletasks()
        self._layout()
        self.overlay.deiconify()
        try:
            self.overlay.attributes("-alpha", 0.8)       # some systems apply it only once mapped
        except tk.TclError:
            pass
        self.top.deiconify()
        self.overlay.lift()
        self.top.lift()
        Dialog._open.append(self)
        self.top.focus_force()
        if focus:
            self.top.after(60, focus)
        self.top.after(80, self._grab)

    def _grab(self):
        try:
            if not self.closed:
                self.top.grab_set()
        except tk.TclError:
            pass

    def close(self):
        if self.closed:
            return
        self.closed = True
        for p in list(Popup.opened):
            p.close()
        try:
            self.app.root.unbind("<Configure>", self._cfg)
        except Exception:
            pass
        for w in (self.top, self.overlay):
            try:
                w.grab_release()
                w.destroy()
            except tk.TclError:
                pass
        if self in Dialog._open:
            Dialog._open.remove(self)
        if self.on_close:
            self.on_close()

    # helpers for forms --------------------------------------------------------
    def label(self, parent, text):
        lb = tk.Label(parent, text=text, font=F(14, "medium"), fg=C["foreground"], bg=C["background"], anchor="w")
        return lb


# =========================================================================== Toast
class Toast:
    """shadcn toast (bottom-right, max-w-[420px], p-6 pr-8, rounded-md, border, shadow-lg).
    Only one at a time (TOAST_LIMIT = 1); closes after 5 seconds like the Radix default."""
    current = None

    def __init__(self, app, title, description=None, destructive=False, ms=5000):
        if Toast.current is not None:
            Toast.current.close()
        Toast.current = self
        self.app = app
        root = app.root
        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.destructive = destructive
        fill = C["destructive"] if destructive else C["background"]
        border = C["destructive"] if destructive else C["border"]
        fg = C["white"] if destructive else C["foreground"]
        self.W = min(sc(420), root.winfo_width()) - 2 * sc(16)
        under = app.bg_at(root.winfo_width() - sc(16), root.winfo_height() - sc(16))
        if Dialog._open:
            under = mix("#000000", under, 0.2)
        key = "#ff00fe" if IS_WIN else under
        self.cv = tk.Canvas(self.win, bg=key, highlightthickness=0, bd=0, width=self.W)
        self.cv.pack()
        if IS_WIN:
            try:
                self.win.attributes("-transparentcolor", key)
            except tk.TclError:
                pass
        tf, df = F(14, "semibold"), F(14)
        wrap = self.W - sc(24) - sc(32)
        lh = sc(20)                                   # text-sm line height
        y = sc(24) + 1

        def block(text, font, y, color):
            lines = wrap_lines(text, font, wrap)
            for i, ln in enumerate(lines):
                self.cv.create_text(sc(24) + 1, y + i * lh + lh // 2, text=ln, anchor="w", font=font, fill=color)
            return y + len(lines) * lh
        title = title.replace("\ufe0f", "")
        y = block(title, tf, y, fg)
        if description:
            y = block(description, df, y + sc(4), mix(fill, fg, 0.9))
        H = y + sc(24) + 1
        self.cv.configure(height=H)
        self.H = H
        ids = gfx.draw_box(self.cv, 0, 0, self.W, H, sc(R_MD), fill, border)
        for i in ids:
            self.cv.tag_lower(i)
        self._close_col = (mix(fill, C["white"], 0.6) if destructive else mix(fill, fg, 0.5))
        self.cv.bind("<Enter>", lambda e: self._xbtn(True))
        self.cv.bind("<Leave>", lambda e: self._xbtn(False))
        self.cv.tag_bind("x", "<ButtonRelease-1>", lambda e: self.close())
        self.closed = False
        self.t = 0
        self._place(0)
        self.win.deiconify()
        self.win.lift()
        self.win.attributes("-topmost", True)
        self._anim()
        self.win.after(ms, self.close)

    def _xbtn(self, show):
        self.cv.delete("x")
        if show:
            self.cv.create_image(self.W - sc(8) - sc(4), sc(8) + sc(4), anchor="ne",
                                 image=gfx.icon("x", sc(16), self._close_col), tags="x")

    def _place(self, frac):
        root = self.app.root
        x = root.winfo_rootx() + root.winfo_width() - sc(16) - self.W
        y_end = root.winfo_rooty() + root.winfo_height() - sc(16) - self.H
        y = int(y_end + (1 - frac) * (self.H + sc(16)))
        self.win.geometry("%dx%d+%d+%d" % (self.W, self.H, x, y))

    def _anim(self):
        if self.closed:
            return
        self.t += 1
        f = min(1.0, self.t / 8.0)
        self._place(1 - (1 - f) ** 3)
        if f < 1:
            self.win.after(16, self._anim)

    def close(self):
        if self.closed:
            return
        self.closed = True
        if Toast.current is self:
            Toast.current = None
        try:
            self.win.destroy()
        except tk.TclError:
            pass


# =========================================================================== buttons drawn on a canvas
class CvButton:
    """A shadcn ghost / outline / gradient button drawn as items on an existing canvas, so it can sit on
    cards that fade (opacity-70) or move (hover lift).

    hover_bg may be a colour or ("alpha", colour, a) for semi-transparent hovers on gradients.
    """
    _n = 0

    def __init__(self, cv, text="", icon=None, command=None, variant="ghost", size="sm", fg=None, hover_fg=None,
                 hover_bg=None, gap=12, icon_size=16, font=None, tint=None, under=None, width=None, height=None,
                 padx=None, icon_color=None, disabled=False):
        CvButton._n += 1
        self.tag = "cvbtn%d" % CvButton._n
        self.cv, self.text, self.icon, self.command = cv, text, icon, command
        self.variant, self.fg = variant, fg or C["foreground"]
        self.hover_fg = hover_fg
        self.hover_bg = hover_bg if hover_bg is not None else C["accent"]
        self.t = tint or (lambda c: c)
        self.under = under
        self.font = font or F(14, "medium")
        self.isz = sc(icon_size)
        self.gap = sc(gap) if (text and icon) else 0
        self.h = sc(height) if height else sc(36 if size == "sm" else 40)
        self.padx = sc(padx) if padx is not None else sc(12 if size == "sm" else 16)
        tw = self.font.measure(text) if text else 0
        self.w = sc(width) if width else self.padx * 2 + tw + (self.isz if icon else 0) + self.gap
        self.icon_color = icon_color
        self.hover = False
        self.disabled = disabled
        self.angle = 0.0
        self.x = self.y = 0
        self.visible = False
        btns = getattr(cv, "_cvbuttons", None)
        if btns is None:                      # one set of handlers per canvas (hit-testing by rectangle)
            btns = cv._cvbuttons = []
            cv.bind("<Motion>", lambda e, c=cv: CvButton._motion(c, e), add="+")
            cv.bind("<Leave>", lambda e, c=cv: CvButton._motion(c, None), add="+")
            cv.bind("<ButtonRelease-1>", lambda e, c=cv: CvButton._release(c, e), add="+")
        btns.append(self)

    def contains(self, x, y):
        return self.visible and self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    @staticmethod
    def _motion(cv, e):
        hit = None
        if e is not None:
            x, y = cv.canvasx(e.x), cv.canvasy(e.y)
            for b in cv._cvbuttons:
                if b.contains(x, y) and not b.disabled:
                    hit = b
        changed = False
        for b in cv._cvbuttons:
            v = b is hit
            if b.hover != v:
                b.hover = v
                b.draw()
                changed = True
        if changed:
            cv.configure(cursor="hand2" if hit else "")

    @staticmethod
    def _release(cv, e):
        x, y = cv.canvasx(e.x), cv.canvasy(e.y)
        for b in list(cv._cvbuttons):
            if b.contains(x, y) and not b.disabled and b.command:
                b.command()
                return

    def place(self, x, y):
        self.x, self.y = int(x), int(y)
        self.visible = True
        self.draw()
        return self

    def remove(self):
        self.cv.delete(self.tag)
        if self in getattr(self.cv, "_cvbuttons", []):
            self.cv._cvbuttons.remove(self)

    def draw(self):
        cv, t = self.cv, self.t
        cv.delete(self.tag)
        x, y, w, h = self.x, self.y, self.w, self.h
        fg = self.fg
        hov = self.hover and not self.disabled
        if self.variant == "gradient":
            cv.create_image(x, y, anchor="nw", tags=self.tag,
                            image=gfx.gradient_box(w, h, sc(R_MD), t(C["primary"]), t(C["accent"]), 0.9 if hov else 1))
        elif self.variant == "outline":
            fill = t(C["accent"]) if hov else t(C["background"])
            gfx.draw_box(cv, x, y, x + w, y + h, sc(R_MD), fill, t(C["accent"] if hov else C["input"]), tags=self.tag)
            if hov:
                fg = self.hover_fg or C["accent_fg"]
        else:
            if hov:
                hb = self.hover_bg
                if isinstance(hb, tuple):
                    cv.create_image(x, y, anchor="nw", tags=self.tag,
                                    image=gfx.gradient_box(w, h, sc(R_MD), hb[1], hb[1], hb[2]))
                else:
                    gfx.draw_box(cv, x, y, x + w, y + h, sc(R_MD), t(hb), tags=self.tag)
                fg = self.hover_fg or C["accent_fg"]

        if self.disabled and self.under:
            fg = mix(self.under, fg, 0.5)
        fg = t(fg)
        tw = self.font.measure(self.text) if self.text else 0
        total = tw + (self.isz + self.gap if self.icon else 0)
        cx = x + (w - total) / 2.0
        if self.icon:
            ic = fg if (hov or not self.icon_color) else t(self.icon_color)
            cv.create_image(int(cx), y + h // 2, anchor="w", tags=self.tag,
                            image=gfx.icon(self.icon, self.isz, ic, angle=self.angle))
            cx += self.isz + self.gap
        if self.text:
            cv.create_text(int(cx), y + h // 2, anchor="w", text=self.text, fill=fg, font=self.font, tags=self.tag)


class HoverWatch:
    """Calls on_change(True/False) when the pointer enters / leaves a widget, including its child widgets
    (tk sends <Leave> when the pointer moves onto an embedded entry, so the position is polled)."""

    def __init__(self, widget, on_change):
        self.w, self.cb, self.inside, self._job = widget, on_change, False, None
        widget.bind("<Enter>", self._enter, add="+")

    def _enter(self, e=None):
        if not self.inside:
            self.inside = True
            self.cb(True)
        if self._job is None:
            self._job = self.w.after(60, self._poll)

    def _poll(self):
        self._job = None
        try:
            if not self.w.winfo_exists():
                return
            px, py = self.w.winfo_pointerxy()
            x, y = self.w.winfo_rootx(), self.w.winfo_rooty()
            inside = (x <= px < x + self.w.winfo_width() and y <= py < y + self.w.winfo_height()
                      and self.w.winfo_viewable() and not Dialog._open)
        except tk.TclError:
            return
        if inside:
            self._job = self.w.after(60, self._poll)
        elif self.inside:
            self.inside = False
            self.cb(False)


class FieldLabel(tk.Canvas):
    """shadcn <Label> (text-sm font-medium leading-none) inside a block: the line box is 24 px tall."""

    def __init__(self, parent, text, bg=None):
        bg = bg or parent.cget("bg")
        super().__init__(parent, height=sc(24), bg=bg, highlightthickness=0, bd=0)
        self.create_text(0, sc(24) // 2 + 1, anchor="w", text=text, font=F(14, "medium"), fill=C["foreground"])
