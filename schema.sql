-- StudyPro database schema (SQLite)
-- The web version kept these records in the browser's localStorage under the keys
-- studypro_users, studypro_session, studypro_tasks_<userId>, studypro_subtasks_<taskId>,
-- studypro_exams_<userId> and studypro_timetable_<userId>. Each key is now a table.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,                 -- UUID, like crypto.randomUUID()
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,                    -- PBKDF2-SHA256 (the web stored plain text)
    salt          TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- the logged-in user ("studypro_session"); at most one row
CREATE TABLE IF NOT EXISTS session (
    id         INTEGER PRIMARY KEY CHECK (id = 1),
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    logged_in  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT NOT NULL,
    subject    TEXT NOT NULL,
    deadline   TEXT NOT NULL,                       -- YYYY-MM-DD
    priority   TEXT NOT NULL CHECK (priority IN ('High', 'Medium', 'Low')),
    status     TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed')),
    type       TEXT NOT NULL CHECK (type IN ('Online', 'Offline')),
    progress   INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subtasks (
    id        TEXT PRIMARY KEY,
    task_id   TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    name      TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
    position  INTEGER NOT NULL DEFAULT 0            -- keeps the order they were added in
);

CREATE TABLE IF NOT EXISTS exams (
    id        TEXT PRIMARY KEY,
    user_id   TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject   TEXT NOT NULL,
    exam_date TEXT NOT NULL                         -- YYYY-MM-DD
);

CREATE TABLE IF NOT EXISTS timetable (
    id        TEXT PRIMARY KEY,
    user_id   TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day       TEXT NOT NULL CHECK (day IN ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')),
    time_slot TEXT NOT NULL,                        -- e.g. "09:00 AM - 10:00 AM"
    subject   TEXT NOT NULL,
    position  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_tasks_user     ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_subtasks_task  ON subtasks(task_id);
CREATE INDEX IF NOT EXISTS idx_exams_user     ON exams(user_id);
CREATE INDEX IF NOT EXISTS idx_timetable_user ON timetable(user_id);
