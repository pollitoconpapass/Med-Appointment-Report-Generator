import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager


class Database:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.getenv(
                "DATABASE_PATH",
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "marge.db",
                ),
            )
        self.db_path = db_path
        self.create_tables()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def create_tables(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    username      TEXT    UNIQUE NOT NULL,
                    email         TEXT    UNIQUE NOT NULL,
                    password_hash TEXT    NOT NULL,
                    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
                    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id            TEXT PRIMARY KEY,
                    user_id       INTEGER REFERENCES users(id),
                    language      TEXT    NOT NULL DEFAULT 'en',
                    num_speakers  INTEGER DEFAULT 2,
                    min_speakers  INTEGER,
                    max_speakers  INTEGER,
                    status        TEXT    NOT NULL DEFAULT 'active',
                    started_at    TEXT    NOT NULL DEFAULT (datetime('now')),
                    ended_at      TEXT,
                    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS transcriptions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT    NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    speaker     TEXT,
                    text        TEXT    NOT NULL,
                    timestamp   REAL,
                    chunk_start REAL,
                    chunk_end   REAL,
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS reports (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT    NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    content     TEXT    NOT NULL DEFAULT '',
                    status      TEXT    NOT NULL DEFAULT 'draft',
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_user_id
                    ON sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_status
                    ON sessions(status);
                CREATE INDEX IF NOT EXISTS idx_transcriptions_session_id
                    ON transcriptions(session_id);
                CREATE INDEX IF NOT EXISTS idx_reports_session_id
                    ON reports(session_id);
            """)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def create_user(self, username: str, email: str, password_hash: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash),
            )
            return cursor.lastrowid

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
            return dict(row) if row else None

    def update_user(self, user_id: int, **kwargs) -> bool:
        allowed = {"username", "email", "password_hash"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?", values
            )
            return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_session(
        self,
        session_id: str,
        user_id: Optional[int] = None,
        language: str = "en",
        num_speakers: int = 2,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        started_at: Optional[str] = None,
    ) -> bool:
        if started_at is None:
            started_at = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO sessions
                   (id, user_id, language, num_speakers, min_speakers, max_speakers, started_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, user_id, language, num_speakers,
                 min_speakers, max_speakers, started_at),
            )
            return True

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_session(self, session_id: str, **kwargs) -> bool:
        allowed = {
            "language", "num_speakers", "min_speakers",
            "max_speakers", "status", "ended_at",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [session_id]
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE sessions SET {set_clause} WHERE id = ?", values
            )
            return cursor.rowcount > 0

    def end_session(self, session_id: str) -> bool:
        return self.update_session(
            session_id, status="completed", ended_at=datetime.now().isoformat()
        )

    def delete_session(self, session_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE id = ?", (session_id,)
            )
            return cursor.rowcount > 0

    def get_user_sessions(
        self, user_id: int, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM sessions WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                    (user_id, status),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                ).fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Transcriptions
    # ------------------------------------------------------------------

    def add_transcription(
        self,
        session_id: str,
        speaker: str,
        text: str,
        timestamp: float,
        chunk_start: float,
        chunk_end: float,
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO transcriptions
                   (session_id, speaker, text, timestamp, chunk_start, chunk_end)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, speaker, text, timestamp, chunk_start, chunk_end),
            )
            return cursor.lastrowid

    def add_transcriptions_bulk(
        self, session_id: str, transcriptions: List[Dict[str, Any]]
    ) -> int:
        with self.get_connection() as conn:
            values = [
                (
                    session_id,
                    t.get("speaker"),
                    t.get("text", ""),
                    t.get("timestamp", 0.0),
                    t.get("chunk_start", 0.0),
                    t.get("chunk_end", 0.0),
                )
                for t in transcriptions
            ]
            conn.executemany(
                """INSERT INTO transcriptions
                   (session_id, speaker, text, timestamp, chunk_start, chunk_end)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                values,
            )
            return len(values)

    def get_session_transcriptions(self, session_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM transcriptions WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_session_transcriptions(self, session_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM transcriptions WHERE session_id = ?", (session_id,)
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def create_report(self, session_id: str, content: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO reports (session_id, content) VALUES (?, ?)",
                (session_id, content),
            )
            return cursor.lastrowid

    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reports WHERE id = ?", (report_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_session_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reports WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_user_reports(
        self, user_id: int, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            query = """
                SELECT r.id, r.session_id, r.status, r.created_at, r.updated_at,
                       s.started_at, s.language
                FROM reports r
                JOIN sessions s ON r.session_id = s.id
                WHERE s.user_id = ?
            """
            params: list = [user_id]
            if status:
                query += " AND r.status = ?"
                params.append(status)
            query += " ORDER BY r.created_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_report_with_session(self, report_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                """SELECT r.*, s.user_id, s.started_at, s.language,
                          s.status as session_status
                   FROM reports r
                   JOIN sessions s ON r.session_id = s.id
                   WHERE r.id = ?""",
                (report_id,),
            ).fetchone()
            return dict(row) if row else None

    def update_report(
        self, report_id: int, content: str, status: Optional[str] = None
    ) -> bool:
        updates = {"content": content, "updated_at": datetime.now().isoformat()}
        if status:
            updates["status"] = status
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [report_id]
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE reports SET {set_clause} WHERE id = ?", values
            )
            return cursor.rowcount > 0

    def delete_report(self, report_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM reports WHERE id = ?", (report_id,)
            )
            return cursor.rowcount > 0

    def delete_session_report(self, session_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM reports WHERE session_id = ?", (session_id,)
            )
            return cursor.rowcount > 0
