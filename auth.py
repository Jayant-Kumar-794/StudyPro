"""Login.tsx and Register.tsx: gradient background with a centred white card."""
import tkinter as tk

from .. import gfx
from ..models import AuthService
from ..store import set_session
from ..theme import C, F, sc, mix, gradient_at
from ..widgets import Input, Button

FIELD = 88                     # label line (24) + gap (8) + input (40) + space-y-4 (16)


class AuthPage(tk.Canvas):
    MODES = {
        "login": dict(heading="Welcome back", button="Login", icon="log-in", question="Don't have an account?",
                      link="Register", fields=[("Email", "john@example.com", False),
                                               ("Password", "•" * 8, True)]),
        "register": dict(heading="Create your account", button="Register", icon="user-plus",
                         question="Already have an account?", link="Login",
                         fields=[("Full Name", "John Doe", False), ("Email", "john@example.com", False),
                                 ("Password", "•" * 8, True)]),
    }

    def __init__(self, app, mode="login"):
        super().__init__(app.root, bg=C["primary"], highlightthickness=0, bd=0)
        self.app, self.mode = app, mode
        self.cfg = self.MODES[mode]
        self.inputs, self.wins = [], []
        for label, ph, pw in self.cfg["fields"]:
            inp = Input(self, placeholder=ph, password=pw, bg=C["card"], on_enter=self.submit)
            self.inputs.append(inp)
            self.wins.append(self.create_window(0, 0, window=inp, anchor="nw"))
        self.btn = Button(self, self.cfg["button"], self.submit, icon=self.cfg["icon"], bg=C["card"])
        self.btn_win = self.create_window(0, 0, window=self.btn, anchor="nw")
        self.link_hover = False
        self.link_box = None
        # hit-test by position: redrawing an item under the mouse with tag Enter/Leave bindings loops forever
        self.bind("<Motion>", lambda e: self._link(self._on_link(e)))
        self.bind("<Leave>", lambda e: self._link(False))
        self.bind("<ButtonRelease-1>", lambda e: self._on_link(e) and self.app.show(
            "register" if mode == "login" else "login"))
        self._size = None
        self.bind("<Configure>", self._on_cfg)
        self.after(50, self.inputs[0].focus)

    def card_height(self):
        return sc(156) + len(self.inputs) * sc(FIELD) + sc(40 + 24 + 20 + 32)

    def _on_link(self, e):
        b = self.link_box
        return bool(b and b[0] <= e.x <= b[2] and b[1] <= e.y <= b[3])

    def _link(self, v):
        if v == self.link_hover:
            return
        self.link_hover = v
        self.configure(cursor="hand2" if v else "")
        self.draw_card()

    def _on_cfg(self, e):
        size = (self.winfo_width(), self.winfo_height())
        if size == self._size:
            return
        self._size = size
        W, H = size
        gfx.gradient_lines(self, W, H, C["primary"], C["hero_end"], tag="bg", step=3)   # .gradient-hero
        self.draw_card()

    def bg_at(self, x, y):
        W, H = self._size or (1, 1)
        return gradient_at((x + y) / float(W + H), C["primary"], C["hero_end"])

    def draw_card(self):
        self.delete("card")
        W, H = self._size
        cw = min(sc(448), W - sc(32))
        ch = self.card_height()
        x1 = (W - cw) // 2
        y1 = max(sc(16), (H - ch) // 2)
        x2 = x1 + cw
        gfx.draw_box(self, x1, y1, x2, y1 + ch, sc(16), C["card"], tags="card")       # rounded-2xl
        # logo: w-10 h-10 rounded-xl gradient-primary + BookOpen, "StudyPro" text-2xl bold, gap-3
        f = F(24, "bold")
        gw = sc(40) + sc(12) + f.measure("StudyPro")
        lx = (x1 + x2 - gw) // 2
        ly = y1 + sc(32)
        self.create_image(lx, ly, anchor="nw", image=gfx.gradient_box(sc(40), sc(40), sc(12), C["primary"], C["accent"]),
                          tags="card")
        self.create_image(lx + sc(20), ly + sc(20), image=gfx.icon("book-open", sc(20), C["primary_fg"]), tags="card")
        self.create_text(lx + sc(52), ly + sc(20), anchor="w", text="StudyPro", font=f, fill=C["card_fg"], tags="card")
        self.create_text((x1 + x2) // 2, y1 + sc(118), text=self.cfg["heading"], font=F(20, "semibold"),
                         fill=C["card_fg"], tags="card")
        fx1, fx2 = x1 + sc(32), x2 - sc(32)
        y = y1 + sc(156)
        for (label, _ph, _pw), inp, win in zip(self.cfg["fields"], self.inputs, self.wins):
            self.create_text(fx1, y + sc(13), anchor="w", text=label, font=F(14, "medium"), fill=C["card_fg"],
                             tags="card")
            self.coords(win, fx1 - inp.m, y + sc(32) - inp.m)
            self.itemconfigure(win, width=fx2 - fx1 + 2 * inp.m)
            y += sc(FIELD)
        self.coords(self.btn_win, fx1, y)
        self.itemconfigure(self.btn_win, width=fx2 - fx1)
        y += sc(40 + 24)
        q, link = self.cfg["question"] + " ", self.cfg["link"]
        fq, fl = F(14), F(14, "medium", underline=self.link_hover)
        tw = fq.measure(q) + fl.measure(link)
        tx = (x1 + x2 - tw) // 2
        self.create_text(tx, y + sc(10), anchor="w", text=q, font=fq, fill=C["muted_fg"], tags="card")
        lid = self.create_text(tx + fq.measure(q), y + sc(10), anchor="w", text=link, font=fl, fill=C["primary"],
                               tags=("card", "link"))
        self.link_box = self.bbox(lid)

    # ------------------------------------------------------------------ actions
    def submit(self):
        vals = [i.get() for i in self.inputs]
        if not all(vals):
            self.app.toast("All fields are required", destructive=True)
            return
        if self.mode == "login":
            r = AuthService.validate_login(vals[0], vals[1])
            if isinstance(r, str):
                self.app.toast("Invalid email or password", destructive=True)
                return
            self.app.show("dashboard", user=r.as_dict(), alert=True)
            self.app.toast("Welcome back, %s!" % r.name)
        else:
            r = AuthService.register(vals[0], vals[1], vals[2])
            if isinstance(r, str):
                self.app.toast(r, destructive=True)
                return
            set_session(r.as_dict())
            self.app.show("dashboard", user=r.as_dict(), alert=True)
            self.app.toast("Account created!")
