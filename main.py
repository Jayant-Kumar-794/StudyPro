"""StudyPro - Student Task & Exam Manager (Python + tkinter + SQLite)

Run:   python main.py

The desktop version of the StudyPro web app (React + Tailwind). It looks the same and saves
everything in an SQLite database (database/studypro.db) instead of the browser's localStorage.
Demo login:  aarav@student.edu  /  study123      (reset the demo data with: python database/seed.py)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def enable_dpi_awareness():
    """Sharp text on Windows screens with 125 % / 150 % scaling."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def main():
    if sys.version_info < (3, 8):
        sys.exit("StudyPro needs Python 3.8 or newer.")
    try:
        import tkinter  # noqa: F401
    except ImportError:
        sys.exit("tkinter is missing. Re-install Python from python.org and tick 'tcl/tk and IDLE'.")
    enable_dpi_awareness()
    from database import get_db
    from database.db_connection import DB_PATH
    first_run = not os.path.exists(DB_PATH)
    if first_run:                                  # no database yet: create it with the demo student
        from database.seed import reset
        reset()
    get_db()
    from studypro.app import App
    App().run()


if __name__ == "__main__":
    main()
