"""Database connection for StudyPro.

One small class wraps Python's built-in sqlite3 module:

* opens database/studypro.db (created automatically with schema.sql the first time),
* turns on foreign keys so deleting a task also deletes its subtasks,
* returns rows as dictionaries (sqlite3.Row),
* offers execute / query / query_one helpers and a transaction() context manager
  that commits on success and rolls back on an error.

Usage
-----
    from database import get_db
    db = get_db()
    rows = db.query("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
    with db.transaction():
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
"""
import os
import sqlite3
from contextlib import contextmanager

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "studypro.db")
SCHEMA_PATH = os.path.join(HERE, "schema.sql")


class DatabaseConnection:
    def __init__(self, path=DB_PATH):
        self.path = path
        self.conn = None
        self._depth = 0                    # nesting level of transaction()

    # ------------------------------------------------------------------ open / close
    def connect(self):
        if self.conn is None:
            new = not os.path.exists(self.path)
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.init_schema()
            self.created_new = new
        return self.conn

    def close(self):
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    def init_schema(self):
        """Create the tables if they do not exist yet (safe to run every start)."""
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    # ------------------------------------------------------------------ helpers
    def execute(self, sql, params=()):
        cur = self.connect().execute(sql, params)
        if self._depth == 0:
            self.conn.commit()
        return cur

    def executemany(self, sql, seq):
        cur = self.connect().executemany(sql, seq)
        if self._depth == 0:
            self.conn.commit()
        return cur

    def query(self, sql, params=()):
        return [dict(r) for r in self.connect().execute(sql, params).fetchall()]

    def query_one(self, sql, params=()):
        r = self.connect().execute(sql, params).fetchone()
        return dict(r) if r else None

    def scalar(self, sql, params=()):
        r = self.connect().execute(sql, params).fetchone()
        return r[0] if r else None

    @contextmanager
    def transaction(self):
        """Group several statements: all of them are saved, or none if an error happens."""
        conn = self.connect()
        self._depth += 1
        try:
            yield self
            self._depth -= 1
            if self._depth == 0:
                conn.commit()
        except Exception:
            self._depth -= 1
            if self._depth == 0:
                conn.rollback()
            raise

    def table_counts(self):
        return {t: self.scalar("SELECT COUNT(*) FROM %s" % t)
                for t in ("users", "tasks", "subtasks", "exams", "timetable")}


_db = None


def get_db():
    """The shared connection used by the whole app."""
    global _db
    if _db is None:
        _db = DatabaseConnection()
        _db.connect()
    return _db


if __name__ == "__main__":
    db = get_db()
    print("Database:", db.path)
    for table, n in db.table_counts().items():
        print("  %-10s %d rows" % (table, n))
