"""Classes from the project's class diagram (the Python version of src/lib/classes.ts and
cpp/StudyPro.cpp). They wrap the functions in store.py, which talk to the SQLite database.

    User ─ 1..* ─ Task ─ 1..* ─ Subtask
    User ─ 1..* ─ Exam
    User ─ 1..* ─ TimetableEntry
    AuthService, CalendarService, ReminderService, DashboardController
"""
from . import store


class User:
    def __init__(self, data):
        self.id, self.name, self.email = data["id"], data["name"], data["email"]

    @staticmethod
    def register(name, email, password):
        r = store.register_user(name, email, password)
        return r if isinstance(r, str) else User(r)

    @staticmethod
    def login(email, password):
        r = store.login_user(email, password)
        if isinstance(r, str):
            return r
        store.set_session(r)
        return User(r)

    def logout(self):
        store.clear_session()

    def as_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


class Subtask:
    def __init__(self, data):
        self.id, self.task_id, self.name, self.completed = (data["id"], data["taskId"], data["name"],
                                                             data["completed"])

    @staticmethod
    def add_subtask(task_id, name):
        return Subtask(store.add_subtask(task_id, name))

    def edit_subtask(self, name):
        store.update_subtask_name(self.task_id, self.id, name)
        self.name = name

    def delete_subtask(self):
        store.delete_subtask(self.task_id, self.id)

    def toggle_status(self):
        store.toggle_subtask(self.task_id, self.id)
        self.completed = not self.completed


class Task:
    def __init__(self, data):
        self.id = data["id"]
        self.title = data["title"]
        self.subject = data["subject"]
        self.deadline = data["deadline"]
        self.priority = data["priority"]
        self.status = data["status"]
        self.type = data["type"]
        self.progress = data["progress"]
        self.user_id = data["userId"]
        self.created_at = data["createdAt"]

    @staticmethod
    def add_task(user_id, title, subject, deadline, type_, subtask_names):
        return Task(store.add_task(user_id, title, subject, deadline, type_, subtask_names))

    def edit_task(self, **updates):
        d = store.update_task(self.user_id, self.id, **updates)
        if d:
            self.__init__(d)

    def delete_task(self):
        store.delete_task(self.user_id, self.id)

    def calculate_priority(self):
        return store.get_priority(self.calculate_days_left())

    def calculate_days_left(self):
        return store.calc_days_left(self.deadline)

    def get_subtasks(self):
        return [Subtask(s) for s in store.get_subtasks(self.id)]


class Exam:
    def __init__(self, data):
        self.id, self.subject, self.exam_date, self.user_id = (data["id"], data["subject"], data["examDate"],
                                                               data["userId"])

    @staticmethod
    def add_exam(user_id, subject, exam_date):
        return Exam(store.add_exam(user_id, subject, exam_date))

    @staticmethod
    def get_upcoming_exams(user_id):
        ex = [Exam(e) for e in store.get_exams(user_id)]
        ex = [e for e in ex if store.calc_days_left(e.exam_date) >= 0]
        return sorted(ex, key=lambda e: store.calc_days_left(e.exam_date))

    def delete(self):
        store.delete_exam(self.user_id, self.id)


class TimetableEntry:
    def __init__(self, data):
        self.id, self.day, self.time_slot, self.subject, self.user_id = (data["id"], data["day"], data["timeSlot"],
                                                                         data["subject"], data["userId"])

    @staticmethod
    def add_entry(user_id, day, time_slot, subject):
        return TimetableEntry(store.add_timetable_entry(user_id, day, time_slot, subject))

    def edit_entry(self, day, time_slot, subject):
        store.delete_timetable_entry(self.user_id, self.id)
        self.__init__(store.add_timetable_entry(self.user_id, day, time_slot, subject))

    def delete(self):
        store.delete_timetable_entry(self.user_id, self.id)


class AuthService:
    _current = None

    @classmethod
    def current_user(cls):
        if cls._current is None:
            s = store.get_session()
            cls._current = User(s) if s else None
        return cls._current

    @classmethod
    def validate_login(cls, email, password):
        r = User.login(email, password)
        if isinstance(r, str):
            return r
        cls._current = r
        return r

    @staticmethod
    def register(name, email, password):
        return User.register(name, email, password)

    @classmethod
    def logout(cls):
        store.clear_session()
        cls._current = None


class CalendarService:
    """Turns task deadlines and exam dates into calendar events."""

    def __init__(self):
        self.events = []

    def map_deadlines(self, tasks):
        return [{"date": t["deadline"], "label": t["subject"], "type": "assignment",
                 "urgent": store.calc_days_left(t["deadline"]) <= 2} for t in tasks]

    def map_exams(self, exams):
        out = []
        for e in exams:
            d = store.calc_days_left(e["examDate"])
            out.append({"date": e["examDate"], "label": e["subject"], "type": "exam", "urgent": 0 <= d <= 3})
        return out

    def render_calendar(self, tasks, exams):
        self.events = self.map_deadlines(tasks) + self.map_exams(exams)
        return self.events


class ReminderService:
    def check_task_reminder(self, task):
        d = store.calc_days_left(task["deadline"])
        if d < 0:
            return "Overdue: %s" % task["title"]
        if d == 0:
            return "Due today: %s" % task["title"]
        if d <= 2:
            return "%s is due in %d day(s)" % (task["title"], d)
        return ""

    def check_exam_reminder(self, exam):
        d = store.calc_days_left(exam["examDate"])
        if d < 0:
            return ""
        if d == 0:
            return "Exam today: %s" % exam["subject"]
        if d <= 3:
            return "%s exam in %d day(s)" % (exam["subject"], d)
        return ""

    def urgent_counts(self, tasks, exams):
        """Numbers for the '⚠️ Upcoming Deadlines!' toast."""
        ut = sum(1 for t in tasks if store.calc_days_left(t["deadline"]) <= 2 and t["status"] == "pending")
        ue = sum(1 for e in exams if 0 <= store.calc_days_left(e["examDate"]) <= 3)
        return ut, ue


class DashboardController:
    def __init__(self, user_id):
        self.user_id = user_id
        self.tasks, self.exams, self.timetable = [], [], []

    def load_dashboard(self):
        self.tasks = store.get_tasks(self.user_id)
        self.exams = store.get_exams(self.user_id)
        self.timetable = store.get_timetable(self.user_id)

    def refresh_data(self):
        self.load_dashboard()
