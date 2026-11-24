"""SQLite event log. All database calls run on the GUI thread."""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

DB = Path.home() / '.netscope' / 'history.db'


def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB)) as conn, conn:
        conn.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, timestamp TEXT, action TEXT, status TEXT, summary TEXT)')


def save_event(action, status, summary):
    with closing(sqlite3.connect(DB)) as conn, conn:
        conn.execute('INSERT INTO events(timestamp, action, status, summary) VALUES (?, ?, ?, ?)',
                     (datetime.now().isoformat(sep=' ', timespec='seconds'), action, status, summary))


def read_events():
    with closing(sqlite3.connect(DB)) as conn:
        return conn.execute('SELECT timestamp, action, status, summary FROM events ORDER BY id DESC LIMIT 200').fetchall()


def clear_events():
    with closing(sqlite3.connect(DB)) as conn, conn:
        conn.execute('DELETE FROM events')
