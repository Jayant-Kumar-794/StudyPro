"""Application window: switches between the Login, Register and Dashboard screens (App.tsx routes)."""
import sys
import tkinter as tk

from . import gfx, theme
from .models import AuthService
from .theme import C, sc
from .widgets import Toast, Dialog, Popup, wheel_units


class App:
    def __init__(self):
        theme.register_fonts()
        self.root = root = tk.Tk()
        root.withdraw()
        theme.init_scaling(root)
        theme.init_fonts(root)
        root.title("StudyPro")
        root.configure(bg=C["background"])
        self._set_icon()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(sc(1440), int(sw * 0.92)), min(sc(900), int(sh * 0.88))
        root.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, max(0, (sh - h) // 2 - sc(20))))
        root.minsize(min(sc(760), w), min(sc(560), h))
        self.page = None
        self.page_name = None
        root.bind_all("<MouseWheel>", self._wheel)
        root.bind_all("<Button-4>", self._wheel)
        root.bind_all("<Button-5>", self._wheel)
        root.protocol("WM_DELETE_WINDOW", self.quit)
        user = AuthService.current_user()           # remembered login (session table)
        if user:
            self.show("dashboard", user=user.as_dict(), alert=True)
        else:
            self.show("login")
        root.deiconify()

    def _set_icon(self):
        try:
            img = gfx.gradient_box(64, 64, 14, C["primary"], C["accent"])
            book = gfx.icon("book-open", 40, "#ffffff", stroke=2.2)
            icon = tk.PhotoImage(width=64, height=64)
            icon.tk.call(icon, "copy", img)
            icon.tk.call(icon, "copy", book, "-to", 12, 12)
            self._icon = icon
            self.root.iconphoto(True, icon)
        except tk.TclError:
            pass

    # ------------------------------------------------------------------ navigation
    def show(self, name, **kw):
        from .pages.auth import AuthPage
        from .pages.dashboard import Dashboard
        for d in list(Dialog._open):
            d.close()
        old = self.page
        if name == "dashboard":
            page = Dashboard(self, kw["user"], alert=kw.get("alert", False))
        else:
            page = AuthPage(self, name)
        page.pack(fill="both", expand=True)
        self.page, self.page_name = page, name
        if old is not None:
            old.destroy()
        self.root.title("StudyPro" if name == "dashboard" else "StudyPro - %s" % name.capitalize())

    def toast(self, title, description=None, destructive=False):
        self.root.update_idletasks()
        Toast(self, title, description, destructive)

    def bg_at(self, x, y):
        return self.page.bg_at(x, y) if self.page is not None else C["background"]

    # ------------------------------------------------------------------ mouse wheel
    def _wheel(self, e):
        if Dialog._open or Popup.opened or self.page_name != "dashboard":
            return
        units = wheel_units(e)
        if sys.platform == "darwin":
            units = -e.delta
        from .components.task_card import SubtaskList
        w = self.root.winfo_containing(e.x_root, e.y_root)
        while w is not None:
            if isinstance(w, SubtaskList) and w.scroll(units):
                return
            w = w.master
        self.page.scroll.scroll(units)

    def run(self):
        self.root.mainloop()

    def quit(self):
        from database import get_db
        get_db().close()
        self.root.destroy()
