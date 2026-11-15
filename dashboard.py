"""Dashboard.tsx: navbar, welcome text, statistics and the Tasks / Exams / Calendar / Timetable tabs."""
import os
import tkinter as tk

from .. import gfx, store
from ..models import AuthService, DashboardController, ReminderService
from ..theme import C, F, sc, mix, gradient_at, ASSETS
from ..widgets import Input, Select, Button, Tabs, ScrollArea, CvButton
from ..components.stats_bar import StatsBar
from ..components.task_card import TaskCard
from ..components.task_dialog import TaskDialog
from ..components.exam_section import ExamSection
from ..components.calendar_view import CalendarView
from ..components.timetable_section import TimetableSection

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
AUTO_REFRESH_MS = 60000


class NavBar(tk.Canvas):
    """<nav class='gradient-primary sticky top-0'> with logo, Refresh, 'Hi, name' and Logout."""

    def __init__(self, dash):
        super().__init__(dash, height=sc(60), bg=C["primary"], highlightthickness=0, bd=0)
        self.dash = dash
        white = C["primary_fg"]
        self.refresh = CvButton(self, "Refresh", "refresh-cw", dash.refresh, fg=white, hover_fg=white,
                                hover_bg=("alpha", "#ffffff", 0.1))
        self.logout = CvButton(self, "Logout", "log-out", dash.logout, fg=white, hover_fg=white, gap=16,
                               hover_bg=("alpha", "#ffffff", 0.1))
        self._width = None
        self.bind("<Configure>", self._on_cfg)

    def _on_cfg(self, e):
        if self.winfo_width() != self._width:
            self._width = self.winfo_width()
            gfx.gradient_lines(self, self._width, sc(60), C["primary"], C["accent"], tag="bg")
            self.draw()

    def color_at(self, x):
        return gradient_at((x + sc(30)) / float(self._width + sc(60)))

    def draw(self):
        self.delete("fg")
        W = self._width or self.winfo_width()
        cw = sc(1400) if W >= sc(1400) else W               # .container (2xl: 1400px)
        x1 = (W - cw) // 2 + sc(16)
        x2 = (W + cw) // 2 - sc(16)
        cy = sc(30)
        self.create_image(x1, cy, anchor="w", image=gfx.alpha_box(sc(32), sc(32), sc(12), "#ffffff", 0.2), tags="fg")
        self.create_image(x1 + sc(16), cy, image=gfx.icon("book-open", sc(16), C["primary_fg"]), tags="fg")
        self.create_text(x1 + sc(44), cy, anchor="w", text="StudyPro", font=F(18, "bold"), fill=C["primary_fg"],
                         tags="fg")
        lo = self.logout
        lo.place(x2 - lo.w, cy - lo.h // 2)
        hi = "Hi, %s" % self.dash.user["name"]
        f = F(14)
        tx = x2 - lo.w - sc(12) - f.measure(hi)
        self.create_text(tx, cy, anchor="w", text=hi, font=f, fill=mix(self.color_at(tx), "#ffffff", 0.8), tags="fg")
        rf = self.refresh
        rf.under = self.color_at(tx - sc(12) - rf.w // 2)
        rf.place(tx - sc(12) - rf.w, cy - rf.h // 2)


class WelcomeHeader(tk.Canvas):
    def __init__(self, parent, name):
        super().__init__(parent, height=sc(56), bg=C["background"], highlightthickness=0, bd=0)
        f = F(24, "bold")
        text = "Welcome back, %s " % name
        self.create_text(0, sc(16), anchor="w", text=text, font=f, fill=C["foreground"])
        self.wave = self._wave_image()
        if self.wave:
            self.create_image(f.measure(text), sc(16), anchor="w", image=self.wave)
        self.create_text(0, sc(32 + 12), anchor="w", text="Your academic overview", font=F(16), fill=C["muted_fg"])

    @staticmethod
    def _wave_image():
        want = sc(24)
        best = min((24, 30, 36, 48), key=lambda s: abs(s - want))
        path = os.path.join(ASSETS, "wave_%d.png" % best)
        try:
            return tk.PhotoImage(file=path)
        except tk.TclError:
            return None


class EmptyTasks(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, height=sc(64 + 48 + 16 + 28 + 24 + 64), bg=C["background"], highlightthickness=0, bd=0)
        self.bind("<Configure>", lambda e: self.draw())

    def draw(self):
        self.delete("all")
        cx = self.winfo_width() // 2
        self.create_image(cx, sc(64 + 24), image=gfx.icon("circle-alert", sc(48), C["muted_fg"]))
        self.create_text(cx, sc(64 + 48 + 16 + 14), text="No tasks available", font=F(18, "semibold"),
                         fill=C["foreground"])
        self.create_text(cx, sc(64 + 48 + 16 + 28 + 12), text="Add your first task to get started!", font=F(16),
                         fill=C["muted_fg"])


class Dashboard(tk.Frame):
    def __init__(self, app, user, alert=False):
        super().__init__(app.root, bg=C["background"])
        self.app, self.user = app, user
        self.controller = DashboardController(user["id"])
        self.tasks, self.exams, self.timetable = [], [], []
        self.filter, self.sort, self.search = "all", "deadline", ""
        self.tab = "tasks"
        self.cards = {}
        self.card_order = []
        self.cols = 3
        self.refreshing = False
        self._snapshot = None

        self.nav = NavBar(self)
        self.nav.pack(fill="x", side="top")
        self.scroll = ScrollArea(self, C["background"])
        self.scroll.pack(fill="both", expand=True)
        body = self.scroll.body
        self.col = tk.Frame(body, bg=C["background"])
        self.col.pack(fill="x")
        body.bind("<Configure>", lambda e: self._layout(), add="+")
        self.scroll.canvas.bind("<Configure>", lambda e: self._layout(), add="+")

        bg = C["background"]
        WelcomeHeader(self.col, user["name"]).pack(fill="x", padx=sc(8), pady=(sc(24), 0))
        self.stats = StatsBar(self.col)
        self.stats.pack(fill="x", pady=(sc(16), 0))
        self.tabs = Tabs(self.col, [("tasks", "Tasks"), ("exams", "Exams"), ("calendar", "Calendar"),
                                    ("timetable", "Timetable")], "tasks", self.set_tab)
        self.tabs.pack(anchor="w", padx=sc(8), pady=(sc(16), 0))
        self.content = tk.Frame(self.col, bg=bg)
        self.content.pack(fill="x", pady=(sc(16), 0))
        tk.Frame(self.col, height=sc(16), bg=bg).pack(fill="x")          # py-6 at the bottom

        # tasks tab --------------------------------------------------------------------
        self.tasks_view = tk.Frame(self.content, bg=bg)
        bar = tk.Frame(self.tasks_view, bg=bg)
        bar.pack(fill="x", padx=sc(4))
        self.add_btn = Button(bar, "Add Task", self.add_task, icon="plus", bg=bg)
        self.add_btn.pack(side="right", padx=(sc(8), sc(4)))
        self.sort_sel = Select(bar, [("deadline", "Sort: Deadline"), ("priority", "Sort: Priority")], "deadline",
                               on_change=self._set_sort, width=150, bg=bg)
        self.sort_sel.pack(side="right", padx=(sc(4), 0))
        self.filter_sel = Select(bar, [("all", "All Tasks"), ("pending", "Pending"), ("completed", "Completed")],
                                 "all", on_change=self._set_filter, width=140, bg=bg)
        self.filter_sel.pack(side="right", padx=(sc(4), 0))
        self.search_in = Input(bar, placeholder="Search tasks...", icon="search", bg=bg, on_change=self._set_search)
        self.search_in.pack(side="left", fill="x", expand=True)
        self.grid_holder = tk.Frame(self.tasks_view, bg=bg)
        self.grid_holder.pack(fill="x", pady=(sc(4), 0))
        self.grid_frame = None
        self.empty = EmptyTasks(self.tasks_view)

        self.exam_view = ExamSection(self.content, self)
        self.calendar_view = CalendarView(self.content, self)
        self.timetable_view = TimetableSection(self.content, self)
        self.views = {"tasks": self.tasks_view, "exams": self.exam_view, "calendar": self.calendar_view,
                      "timetable": self.timetable_view}
        self.tasks_view.pack(fill="x")

        self.load_all()
        self._auto = self.after(AUTO_REFRESH_MS, self._auto_refresh)
        self._pulse_job = None
        if alert:
            self.after(2500, self.urgent_alert)

    # ------------------------------------------------------------------ layout
    def _layout(self):
        W = self.scroll.canvas.winfo_width()
        if W < 50:
            return
        content = min(W, sc(1152)) - sc(32)
        pad = max(0, (W - content) // 2 - sc(8))
        if getattr(self, "_pad", None) != pad:
            self._pad = pad
            self.col.pack_configure(padx=pad)
        ww = self.app.root.winfo_width()
        cols = 3 if ww >= sc(1024) else (2 if ww >= sc(640) else 1)     # lg:grid-cols-3 / sm:grid-cols-2
        if cols != self.cols:
            self.cols = cols
            self.render_tasks(force=True)
            self.exam_view.render(self.exams, cols)

    def bg_at(self, x, y):
        return C["background"]

    # ------------------------------------------------------------------ data
    def load_all(self):
        """DashboardController.loadDashboard(): read everything from the database and redraw."""
        self.controller.load_dashboard()
        c = self.controller
        self.tasks, self.exams, self.timetable = c.tasks, c.exams, c.timetable
        self._snapshot = self._snap()
        self.stats.update(self.tasks)
        self.render_tasks()
        self.exam_view.render(self.exams, self.cols)
        self.calendar_view.render(self.tasks, self.exams)
        self.timetable_view.render(self.timetable)

    def _snap(self):
        subs = store.get_db().query("SELECT s.id, s.name, s.completed FROM subtasks s JOIN tasks t ON t.id = s.task_id "
                                    "WHERE t.user_id = ?", (self.user["id"],)) if hasattr(store, "get_db") else []
        return (repr(self.tasks), repr(self.exams), repr(self.timetable), repr(subs), store.today())

    def _auto_refresh(self):
        """setInterval(loadAll, 60000): reload, but only redraw when something changed."""
        self.controller.load_dashboard()
        c = self.controller
        old = self._snapshot
        self.tasks, self.exams, self.timetable = c.tasks, c.exams, c.timetable
        if self._snap() != old:
            self.load_all()
        self._auto = self.after(AUTO_REFRESH_MS, self._auto_refresh)

    def displayed_tasks(self):
        r = list(self.tasks)
        if self.filter == "completed":
            r = [t for t in r if t["status"] == "completed"]
        if self.filter == "pending":
            r = [t for t in r if t["status"] == "pending"]
        q = self.search.strip().lower()
        if q:
            r = [t for t in r if q in t["title"].lower() or q in t["subject"].lower()]
        if self.sort == "deadline":
            r.sort(key=lambda t: store.calc_days_left(t["deadline"]))
        else:
            r.sort(key=lambda t: PRIORITY_ORDER[t["priority"]])
        return r

    def render_tasks(self, force=False):
        shown = self.displayed_tasks()
        ids = [t["id"] for t in shown]
        if not shown:
            if self.grid_frame is not None:
                self.grid_frame.destroy()
                self.grid_frame = None
            self.cards, self.card_order = {}, []
            self.grid_holder.pack_forget()
            self.empty.pack(fill="x")
            return
        self.empty.pack_forget()
        self.grid_holder.pack(fill="x", pady=(sc(4), 0))
        if ids == self.card_order and not force:
            for t in shown:                                   # same cards: update them in place
                self.cards[t["id"]].set_task(t)
            return
        old = self.grid_frame
        g = self.grid_frame = tk.Frame(self.grid_holder, bg=C["background"])
        for i in range(3):
            g.columnconfigure(i, weight=1 if i < self.cols else 0, uniform="c" if i < self.cols else "")
        cards = {}
        for i, t in enumerate(shown):
            card = self.cards.get(t["id"]) if False else None
            card = TaskCard(g, self, t)
            card.grid(row=i // self.cols, column=i % self.cols, sticky="nsew")
            cards[t["id"]] = card
        g.pack(fill="x")
        if old is not None:
            old.destroy()
        self.cards, self.card_order = cards, ids

    # ------------------------------------------------------------------ toolbar
    def _set_filter(self, v):
        self.filter = v
        self.render_tasks()

    def _set_sort(self, v):
        self.sort = v
        self.render_tasks()

    def _set_search(self, v):
        self.search = v
        self.render_tasks()

    def set_tab(self, key):
        self.tab = key
        for k, v in self.views.items():
            v.pack_forget()
        self.views[key].pack(fill="x")
        self.scroll._update()

    # ------------------------------------------------------------------ task actions (Dashboard.tsx handlers)
    def add_task(self):
        TaskDialog(self.app, None, self._handle_add)

    def edit_task(self, task):
        TaskDialog(self.app, task, lambda d: self._handle_edit(task, d))

    def _handle_add(self, d):
        store.add_task(self.user["id"], d["title"], d["subject"], d["deadline"], d["type"], d["subtaskNames"])
        self.load_all()
        self.app.toast("Task added!")

    def _handle_edit(self, task, d):
        store.update_task(self.user["id"], task["id"], title=d["title"], subject=d["subject"], deadline=d["deadline"],
                          type=d["type"])
        self.load_all()
        self.app.toast("Task updated!")

    def delete_task(self, task):
        store.delete_task(self.user["id"], task["id"])
        self.load_all()
        self.app.toast("Task deleted")

    def toggle_complete(self, task):
        store.update_task(self.user["id"], task["id"],
                          status="pending" if task["status"] == "completed" else "completed")
        self.load_all()

    # ------------------------------------------------------------------ navbar
    def refresh(self):
        if self.refreshing:
            return
        self.refreshing = True
        self.nav.refresh.disabled = True
        self.app.toast("Refreshing data...")
        self._spin(0)
        self.after(500, self._refresh_done)

    def _spin(self, i):
        if not self.refreshing:
            self.nav.refresh.angle = 0.0
            self.nav.draw()
            return
        self.nav.refresh.angle = (i * 0.25) % 6.2832          # animate-spin: one turn per second
        self.nav.refresh.draw()
        self.after(40, lambda: self._spin(i + 1))

    def _refresh_done(self):
        self.load_all()
        self.refreshing = False
        self.nav.refresh.disabled = False

    def logout(self):
        AuthService.logout()
        self.app.show("login")

    def urgent_alert(self):
        """ReminderService: '⚠️ Upcoming Deadlines!' when tasks are due within 2 days or exams within 3."""
        if not self.winfo_exists():
            return
        ut, ue = ReminderService().urgent_counts(self.tasks, self.exams)
        if ut + ue > 0:
            self.app.toast("⚠️ Upcoming Deadlines!", "%d urgent task(s), %d exam(s) coming soon!" % (ut, ue),
                           destructive=True)

    def destroy(self):
        try:
            self.after_cancel(self._auto)
        except Exception:
            pass
        super().destroy()
