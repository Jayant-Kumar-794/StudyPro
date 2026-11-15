"""TaskDialog.tsx: 'Add New Task' / 'Edit Task' form."""
import tkinter as tk

from .. import gfx, store
from ..theme import C, F, sc
from ..widgets import Dialog, Input, Select, DateButton, Button, FieldLabel


class SubtaskChip(tk.Canvas):
    """<li class='flex items-center justify-between bg-muted rounded px-3 py-1.5 text-sm'> with an X button."""

    def __init__(self, parent, text, on_remove):
        super().__init__(parent, height=sc(32), bg=C["background"], highlightthickness=0, bd=0, width=10)
        self.text, self.on_remove, self.hover = text, on_remove, False
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: self._set(False))
        self.bind("<ButtonRelease-1>", self._click)

    def _in_x(self, x):
        W = self.winfo_width()
        return W - sc(12) - sc(14) - 2 <= x <= W - sc(12) + 2

    def _set(self, v):
        if v != self.hover:
            self.hover = v
            self.configure(cursor="hand2" if v else "")
            self.draw()

    def _motion(self, e):
        self._set(self._in_x(e.x))

    def _click(self, e):
        if self._in_x(e.x):
            self.on_remove()

    def draw(self):
        self.delete("all")
        W, H = self.winfo_width(), sc(32)
        gfx.draw_box(self, 0, 0, W, H, sc(4), C["muted"])
        self.create_text(sc(12), H // 2, anchor="w", text=self.text, font=F(14), fill=C["foreground"])
        self.create_image(W - sc(12), H // 2, anchor="e",
                          image=gfx.icon("x", sc(14), C["destructive"] if self.hover else C["muted_fg"]))


class TaskDialog(Dialog):
    def __init__(self, app, task, on_save):
        super().__init__(app, "Edit Task" if task else "Add New Task", width=448)
        self.task, self.on_save = task, on_save
        self.subtask_names = []
        b, bg, P = self.body, C["background"], sc(4)
        self.title_in = self._field(b, "Title", "Assignment name")
        self.subject_in = self._field(b, "Subject", "e.g. Mathematics")
        grid = tk.Frame(b, bg=bg)
        grid.pack(fill="x", pady=(sc(12), 0))
        grid.columnconfigure(0, weight=1, uniform="g")
        grid.columnconfigure(1, weight=1, uniform="g")
        c0 = tk.Frame(grid, bg=bg)
        c0.grid(row=0, column=0, sticky="nsew", padx=(0, sc(2)))
        c1 = tk.Frame(grid, bg=bg)
        c1.grid(row=0, column=1, sticky="nsew", padx=(sc(2), 0))
        FieldLabel(c0, "Deadline", bg).pack(fill="x", padx=P)
        deadline = store.parse_local_date(task["deadline"]) if task and task.get("deadline") else None
        self.date_btn = DateButton(c0, deadline, bg=bg)
        self.date_btn.pack(fill="x", padx=P, pady=(sc(8), P))
        FieldLabel(c1, "Type", bg).pack(fill="x", padx=P)
        self.type_sel = Select(c1, [("Online", "Online"), ("Offline", "Offline")], task["type"] if task else "Online",
                               bg=bg)
        self.type_sel.pack(fill="x", pady=(P, 0))
        if task:
            self.title_in.set(task["title"])
            self.subject_in.set(task["subject"])
        else:                                   # subtasks only for new tasks
            FieldLabel(b, "Subtasks", bg).pack(fill="x", padx=P, pady=(sc(12), 0))
            row = tk.Frame(b, bg=bg)
            row.pack(fill="x", pady=(P, 0))
            self.sub_in = Input(row, placeholder="e.g. Research topic", bg=bg, on_enter=self.add_sub)
            add = Button(row, "", self.add_sub, variant="outline", size="sm", icon="plus", bg=bg)
            add.pack(side="right", anchor="n", padx=(sc(4), P), pady=(P, 0))
            self.sub_in.pack(side="left", fill="x", expand=True)
            self.chips = tk.Frame(b, bg=bg)
            self.chips.pack(fill="x", padx=P)
        btns = tk.Frame(b, bg=bg)
        btns.pack(fill="x", padx=P, pady=(sc(12), 0))
        Button(btns, "Update" if task else "Add Task", self.submit, variant="gradient", bg=bg).pack(side="right")
        Button(btns, "Cancel", self.close, variant="outline", bg=bg).pack(side="right", padx=(0, sc(8)))
        for inp in (self.title_in, self.subject_in):
            inp.entry.bind("<Return>", lambda e: (self.submit(), "break")[1])
        self.show(focus=self.title_in.focus)

    def _field(self, parent, label, placeholder):
        bg = C["background"]
        first = not parent.winfo_children()
        FieldLabel(parent, label, bg).pack(fill="x", padx=sc(4), pady=(0 if first else sc(12), 0))
        inp = Input(parent, placeholder=placeholder, bg=bg)
        inp.pack(fill="x", pady=(sc(4), 0))
        return inp

    def add_sub(self):
        name = self.sub_in.get().strip()
        if name:
            self.subtask_names.append(name)
            self.sub_in.set("")
            self.sub_in.focus()
            self._render_chips()

    def remove_sub(self, i):
        del self.subtask_names[i]
        self._render_chips()

    def _render_chips(self):
        for w in self.chips.winfo_children():
            w.destroy()
        for i, name in enumerate(self.subtask_names):
            SubtaskChip(self.chips, name, lambda i=i: self.remove_sub(i)).pack(
                fill="x", pady=(sc(4) if i == 0 else sc(4), 0))
        self.body.update_idletasks()
        self._layout()

    def submit(self):
        title, subject, deadline = self.title_in.get().strip(), self.subject_in.get().strip(), self.date_btn.value
        if not title or not subject or not deadline:
            return                                  # same as the web form: nothing happens
        if self.date_btn.picker:
            self.date_btn.picker.close()
        data = {"title": title, "subject": subject, "deadline": deadline.isoformat(), "type": self.type_sel.value,
                "subtaskNames": list(self.subtask_names)}
        self.close()
        self.on_save(data)
