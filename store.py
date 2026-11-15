"""Data operations (the Python version of src/lib/store.ts).

The functions have the same names and do the same work as in the web app, but they save
to the SQLite database through database/db_connection.py instead of localStorage.
Records are returned as plain dicts with the same field names as the TypeScript interfaces
(id, title, subject, deadline, priority, status, type, progress, userId, createdAt ...).
"""
import datetime as dt
import hashlib
import hmac
import os
import uuid

from database import get_db


def new_id():
    return str(uuid.uuid4())                       # crypto.randomUUID()


# ============================================================ date helpers
def parse_local_date(s):
    """'YYYY-MM-DD' -> date (the web's parseLocalDate)."""
    if not s:
        return dt.date(1970, 1, 1)
    y, m, d = (int(x) for x in s.split("-"))
    return dt.date(y, m, d)


def today():
    return dt.date.today()


def calc_days_left(deadline):
    if not deadline:
        return float("inf")
    return (parse_local_date(deadline) - today()).days


def days_left_label(deadline):
    if not deadline:
        return "No deadline"
    days = calc_days_left(deadline)
    if days < 0:
        return "Overdue"
    if days == 0:
        return "Due Today"
    if days == 1:
        return "1 day left"
    return "%d days left" % days


def get_priority(days):
    """Priority is set automatically from the days left."""
    if days <= 2:
        return "High"
    if days <= 5:
        return "Medium"
    return "Low"


def us_date(s):
    """new Date(...).toLocaleDateString() in en-US: 11/4/2026."""
    d = parse_local_date(s)
    return "%d/%d/%d" % (d.month, d.day, d.year)


# ============================================================ passwords
def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 120_000).hex()
    return h, salt


def check_password(password, pw_hash, salt):
    return hmac.compare_digest(hash_password(password, salt)[0], pw_hash)


# ============================================================ users
def _user(r):
    return {"id": r["id"], "name": r["name"], "email": r["email"]} if r else None


def get_users():
    return [_user(r) for r in get_db().query("SELECT * FROM users ORDER BY created_at")]


def register_user(name, email, password):
    """Returns the new user dict, or an error message string."""
    db = get_db()
    if db.query_one("SELECT id FROM users WHERE email = ?", (email,)):
        return "Email already registered"
    h, salt = hash_password(password)
    uid = new_id()
    db.execute("INSERT INTO users (id, name, email, password_hash, salt) VALUES (?, ?, ?, ?, ?)",
               (uid, name, email, h, salt))
    return {"id": uid, "name": name, "email": email}


def login_user(email, password):
    r = get_db().query_one("SELECT * FROM users WHERE email = ?", (email,))
    if not r or not check_password(password, r["password_hash"], r["salt"]):
        return "Invalid email or password"
    return _user(r)


# ============================================================ session
def set_session(user):
    get_db().execute("INSERT OR REPLACE INTO session (id, user_id, logged_in) VALUES (1, ?, datetime('now'))",
                     (user["id"],))


def get_session():
    return _user(get_db().query_one("SELECT u.* FROM session s JOIN users u ON u.id = s.user_id WHERE s.id = 1"))


def clear_session():
    get_db().execute("DELETE FROM session")


# ============================================================ tasks
def _task(r):
    return {"id": r["id"], "title": r["title"], "subject": r["subject"], "deadline": r["deadline"],
            "priority": r["priority"], "status": r["status"], "type": r["type"], "progress": r["progress"],
            "userId": r["user_id"], "createdAt": r["created_at"]}


def get_tasks(user_id):
    """In the order they were created (like the array in localStorage)."""
    return [_task(r) for r in get_db().query("SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at, rowid",
                                             (user_id,))]


def get_task(task_id):
    r = get_db().query_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
    return _task(r) if r else None


def add_task(user_id, title, subject, deadline, type_, subtask_names):
    db = get_db()
    tid = new_id()
    created = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    with db.transaction():
        db.execute("INSERT INTO tasks (id, user_id, title, subject, deadline, priority, status, type, progress, "
                   "created_at) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, 0, ?)",
                   (tid, user_id, title, subject, deadline, get_priority(calc_days_left(deadline)), type_, created))
        for i, name in enumerate(subtask_names):
            db.execute("INSERT INTO subtasks (id, task_id, name, completed, position) VALUES (?, ?, ?, 0, ?)",
                       (new_id(), tid, name, i))
    return get_task(tid)


_TASK_FIELDS = {"title": "title", "subject": "subject", "deadline": "deadline", "status": "status",
                "type": "type", "progress": "progress", "priority": "priority"}


def update_task(user_id, task_id, **updates):
    if "deadline" in updates:
        updates["priority"] = get_priority(calc_days_left(updates["deadline"]))
    cols = [(c, updates[k]) for k, c in _TASK_FIELDS.items() if k in updates]
    if not cols:
        return get_task(task_id)
    get_db().execute("UPDATE tasks SET %s WHERE id = ? AND user_id = ?" % ", ".join("%s = ?" % c for c, _v in cols),
                     tuple(v for _c, v in cols) + (task_id, user_id))
    return get_task(task_id)


def delete_task(user_id, task_id):
    get_db().execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))   # subtasks cascade


# ============================================================ subtasks
def _sub(r):
    return {"id": r["id"], "taskId": r["task_id"], "name": r["name"], "completed": bool(r["completed"])}


def get_subtasks(task_id):
    return [_sub(r) for r in get_db().query("SELECT * FROM subtasks WHERE task_id = ? ORDER BY position, rowid",
                                            (task_id,))]


def add_subtask(task_id, name):
    db = get_db()
    pos = (db.scalar("SELECT MAX(position) FROM subtasks WHERE task_id = ?", (task_id,)) or 0) + 1
    sid = new_id()
    db.execute("INSERT INTO subtasks (id, task_id, name, completed, position) VALUES (?, ?, ?, 0, ?)",
               (sid, task_id, name, pos))
    return {"id": sid, "taskId": task_id, "name": name, "completed": False}


def update_subtask_name(task_id, subtask_id, name):
    get_db().execute("UPDATE subtasks SET name = ? WHERE id = ? AND task_id = ?", (name, subtask_id, task_id))
    return get_subtasks(task_id)


def toggle_subtask(task_id, subtask_id):
    get_db().execute("UPDATE subtasks SET completed = 1 - completed WHERE id = ? AND task_id = ?",
                     (subtask_id, task_id))
    return get_subtasks(task_id)


def delete_subtask(task_id, subtask_id):
    get_db().execute("DELETE FROM subtasks WHERE id = ? AND task_id = ?", (subtask_id, task_id))
    return get_subtasks(task_id)


def recalc_progress(user_id, task_id):
    """Progress = finished subtasks / all subtasks; 100 % marks the task completed."""
    subs = get_subtasks(task_id)
    if not subs:
        return
    done = sum(1 for s in subs if s["completed"])
    progress = int(done * 100.0 / len(subs) + 0.5)          # Math.round
    update_task(user_id, task_id, progress=progress, status="completed" if progress == 100 else "pending")


# ============================================================ exams
def _exam(r):
    return {"id": r["id"], "subject": r["subject"], "examDate": r["exam_date"], "userId": r["user_id"]}


def get_exams(user_id):
    return [_exam(r) for r in get_db().query("SELECT * FROM exams WHERE user_id = ? ORDER BY rowid", (user_id,))]


def add_exam(user_id, subject, exam_date):
    eid = new_id()
    get_db().execute("INSERT INTO exams (id, user_id, subject, exam_date) VALUES (?, ?, ?, ?)",
                     (eid, user_id, subject, exam_date))
    return {"id": eid, "subject": subject, "examDate": exam_date, "userId": user_id}


def delete_exam(user_id, exam_id):
    get_db().execute("DELETE FROM exams WHERE id = ? AND user_id = ?", (exam_id, user_id))


# ============================================================ timetable
def _tt(r):
    return {"id": r["id"], "day": r["day"], "timeSlot": r["time_slot"], "subject": r["subject"],
            "userId": r["user_id"]}


def get_timetable(user_id):
    return [_tt(r) for r in get_db().query("SELECT * FROM timetable WHERE user_id = ? ORDER BY position, rowid",
                                           (user_id,))]


def add_timetable_entry(user_id, day, time_slot, subject):
    db = get_db()
    pos = (db.scalar("SELECT MAX(position) FROM timetable WHERE user_id = ?", (user_id,)) or 0) + 1
    eid = new_id()
    db.execute("INSERT INTO timetable (id, user_id, day, time_slot, subject, position) VALUES (?, ?, ?, ?, ?, ?)",
               (eid, user_id, day, time_slot, subject, pos))
    return {"id": eid, "day": day, "timeSlot": time_slot, "subject": subject, "userId": user_id}


def delete_timetable_entry(user_id, entry_id):
    get_db().execute("DELETE FROM timetable WHERE id = ? AND user_id = ?", (entry_id, user_id))


def time_slot_key(slot):
    """Sort key for '09:00 AM - 10:00 AM' by real start time (minutes after midnight)."""
    try:
        start = slot.split("-")[0].strip()
        t = dt.datetime.strptime(start.upper().replace(".", ""), "%I:%M %p")
        return (0, t.hour * 60 + t.minute, slot)
    except ValueError:
        try:
            t = dt.datetime.strptime(slot.split("-")[0].strip(), "%H:%M")
            return (0, t.hour * 60 + t.minute, slot)
        except ValueError:
            return (1, 0, slot)
