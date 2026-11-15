"""Fill the database with a demo student so every screen has something to show.

    python database/seed.py          -> reset studypro.db and add the sample data
    python database/seed.py --empty  -> reset studypro.db and leave it empty

Login:  aarav@student.edu  /  study123
Deadlines and exam dates are set relative to today, so the demo always looks current.
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connection import DatabaseConnection, DB_PATH   # noqa: E402
from studypro import store                                       # noqa: E402

USER = ("Aarav Mehta", "aarav@student.edu", "study123")

# (title, subject, days from today, type, [(subtask, done)], status)
TASKS = [
    ("DBMS Mini Project Report", "Database Systems", 1, "Online",
     [("Draw ER diagram", 1), ("Normalise tables", 1), ("Write SQL queries", 0), ("Final report", 0)], None),
    ("OS Assignment 3", "Operating Systems", 0, "Offline", [("Questions 1-5", 1), ("Questions 6-10", 0)], None),
    ("Calculus Problem Set", "Mathematics", 4, "Offline", [("Integration", 1), ("Series", 0), ("Limits", 1)], None),
    ("Physics Lab Record", "Physics", 7, "Offline", [("Experiment 5", 0), ("Experiment 6", 0)], None),
    ("Tkinter Project", "Python Programming", 10, "Online",
     [("Design UI", 1), ("Database", 1), ("Testing", 1), ("Demo video", 0)], None),
    ("Networks Quiz Prep", "Computer Networks", 3, "Online", [], "pending"),
    ("English Essay", "English", -2, "Online", [("First draft", 1), ("Final copy", 1)], None),
]
EXAMS = [("Database Systems", 2), ("Operating Systems", 6), ("Mathematics", 12), ("Physics", 20), ("English", -5)]
TIMETABLE = [
    ("Mon", "09:00 AM - 10:00 AM", "Mathematics"), ("Mon", "11:00 AM - 12:00 PM", "Physics"),
    ("Tue", "09:00 AM - 10:00 AM", "Database Systems"), ("Tue", "02:00 PM - 04:00 PM", "Programming Lab"),
    ("Wed", "10:00 AM - 11:00 AM", "Operating Systems"), ("Thu", "09:00 AM - 10:00 AM", "Computer Networks"),
    ("Thu", "11:00 AM - 12:00 PM", "Mathematics"), ("Fri", "10:00 AM - 11:00 AM", "Database Systems"),
    ("Fri", "01:00 PM - 03:00 PM", "Physics Lab"), ("Sat", "10:00 AM - 11:00 AM", "English"),
]


def reset(path=DB_PATH, sample=True, login=False):
    import database.db_connection as dbc
    for p in (path, path + "-journal"):
        if os.path.exists(p):
            os.remove(p)
    db = DatabaseConnection(path)
    db.connect()
    dbc._db = db                                   # store.py uses this connection
    if not sample:
        return db
    today = dt.date.today()
    with db.transaction():
        u = store.register_user(*USER)
        for i, (title, subject, days, typ, subs, _st) in enumerate(TASKS):
            day = (today + dt.timedelta(days=days)).isoformat()
            t = store.add_task(u["id"], title, subject, day, typ, [s for s, _d in subs])
            # created a little earlier, in this order
            db.execute("UPDATE tasks SET created_at = ? WHERE id = ?",
                       ((dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(days=14, minutes=60 - i)).strftime(
                           "%Y-%m-%dT%H:%M:%S.000Z"), t["id"]))
            for s, (_n, done) in zip(store.get_subtasks(t["id"]), subs):
                if done:
                    store.toggle_subtask(t["id"], s["id"])
            store.recalc_progress(u["id"], t["id"])
        for subject, days in EXAMS:
            store.add_exam(u["id"], subject, (today + dt.timedelta(days=days)).isoformat())
        for day, slot, subject in TIMETABLE:
            store.add_timetable_entry(u["id"], day, slot, subject)
        if login:
            store.set_session(u)
    return db


if __name__ == "__main__":
    empty = "--empty" in sys.argv
    db = reset(sample=not empty)
    print("Database reset:", db.path)
    for table, n in db.table_counts().items():
        print("  %-10s %d rows" % (table, n))
    if not empty:
        print("Login with  %s  /  %s" % (USER[1], USER[2]))
