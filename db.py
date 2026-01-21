"""SQLite helpers for the Smart Student Management System."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "students.db"


def _get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                batch TEXT,
                email TEXT,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date TEXT NOT NULL,
                attendance TEXT NOT NULL,
                emotion TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
            );
            """
        )


def add_student(
    student_id: str,
    name: str,
    batch: Optional[str],
    email: Optional[str],
    phone: Optional[str],
) -> Tuple[bool, str]:
    """Add a student. Returns (success, message)."""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO students (student_id, name, batch, email, phone)
                VALUES (?, ?, ?, ?, ?);
                """,
                (student_id, name, batch, email, phone),
            )
        return True, "Student added."
    except sqlite3.IntegrityError:
        return False, "Student ID already exists."


def update_student(
    student_id: str,
    name: str,
    batch: Optional[str],
    email: Optional[str],
    phone: Optional[str],
) -> bool:
    """Update a student record."""
    with _get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE students
            SET name = ?, batch = ?, email = ?, phone = ?
            WHERE student_id = ?;
            """,
            (name, batch, email, phone, student_id),
        )
        return cur.rowcount > 0


def delete_student(student_id: str) -> bool:
    """Delete a student and related logs."""
    with _get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM students WHERE student_id = ?;",
            (student_id,),
        )
        return cur.rowcount > 0


def get_students() -> List[Dict[str, Optional[str]]]:
    """Return all students."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT student_id, name, batch, email, phone, created_at FROM students;"
        ).fetchall()
    return [dict(row) for row in rows]


def get_student(student_id: str) -> Optional[Dict[str, Optional[str]]]:
    """Return a single student by ID."""
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT student_id, name, batch, email, phone, created_at
            FROM students WHERE student_id = ?;
            """,
            (student_id,),
        ).fetchone()
    return dict(row) if row else None


def add_log(
    student_id: str,
    date: str,
    attendance: str,
    emotion: Optional[str],
    confidence: Optional[float],
) -> None:
    """Add an attendance/emotion log entry."""
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO logs (student_id, date, attendance, emotion, confidence)
            VALUES (?, ?, ?, ?, ?);
            """,
            (student_id, date, attendance, emotion, confidence),
        )


def get_logs(limit: Optional[int] = None) -> List[Dict[str, Optional[str]]]:
    """Return all logs, newest first."""
    query = """
        SELECT id, student_id, date, attendance, emotion, confidence, created_at
        FROM logs
        ORDER BY date DESC, created_at DESC
    """
    if limit:
        query += " LIMIT ?"
    with _get_connection() as conn:
        rows = conn.execute(query, (limit,) if limit else ()).fetchall()
    return [dict(row) for row in rows]


def get_recent_logs(
    student_id: str,
    limit: int = 7,
) -> List[Dict[str, Optional[str]]]:
    """Return the most recent logs for a student."""
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, student_id, date, attendance, emotion, confidence, created_at
            FROM logs
            WHERE student_id = ?
            ORDER BY date DESC, created_at DESC
            LIMIT ?;
            """,
            (student_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]
