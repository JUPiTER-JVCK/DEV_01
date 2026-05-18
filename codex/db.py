"""SQLite persistence — progress, bookmarks, and personal notes."""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".codex" / "progress.db"

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS progress (
    lesson_id TEXT PRIMARY KEY,
    completed_at TEXT,
    time_spent_sec INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id TEXT NOT NULL,
    lesson_title TEXT NOT NULL,
    saved_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        for stmt in _CREATE_SQL.split(";"):
            stmt = stmt.strip()
            if stmt:
                self._conn.execute(stmt)
        self._conn.commit()

    def mark_complete(self, lesson_id: str, seconds: int = 0) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO progress (lesson_id, completed_at, time_spent_sec) VALUES (?,?,?)",
            (lesson_id, datetime.now().isoformat(), seconds),
        )
        self._conn.commit()

    def is_complete(self, lesson_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM progress WHERE lesson_id=?", (lesson_id,)
        ).fetchone()
        return row is not None

    def completed_ids(self) -> set[str]:
        rows = self._conn.execute("SELECT lesson_id FROM progress").fetchall()
        return {r["lesson_id"] for r in rows}

    def completed_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM progress").fetchone()
        return row["c"]

    def add_bookmark(self, lesson_id: str, lesson_title: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO bookmarks (lesson_id, lesson_title, saved_at) VALUES (?,?,?)",
            (lesson_id, lesson_title, datetime.now().isoformat()),
        )
        self._conn.commit()

    def remove_bookmark(self, lesson_id: str) -> None:
        self._conn.execute("DELETE FROM bookmarks WHERE lesson_id=?", (lesson_id,))
        self._conn.commit()

    def is_bookmarked(self, lesson_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM bookmarks WHERE lesson_id=?", (lesson_id,)
        ).fetchone()
        return row is not None

    def get_bookmarks(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM bookmarks ORDER BY saved_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def add_note(self, lesson_id: str, content: str) -> None:
        self._conn.execute(
            "INSERT INTO notes (lesson_id, content, created_at) VALUES (?,?,?)",
            (lesson_id, content, datetime.now().isoformat()),
        )
        self._conn.commit()

    def get_notes(self, lesson_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM notes WHERE lesson_id=? ORDER BY created_at DESC",
            (lesson_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_notes(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM notes ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()
