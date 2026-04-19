"""SQLite database access for SSMS.

Student records live in the ``students`` table. Each row stores identity and programme as:

- ``student_code`` — unique ID (e.g. S001)
- ``name``, ``email`` (unique)
- ``course`` — programme name (e.g. BSc Computer Science), plain text
- ``year``, ``status``, ``attendance_rate``, ``risk_level``, ``gpa``, ``created_at``

Logins are in ``users`` (``role`` = admin | lecturer | student); students link via ``student_row_id``.
"""
from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# Default: project_root/streamlit_ssms/data/ssms.db
_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = _ROOT / "data" / "ssms.db"


def get_db_path() -> Path:
    p = os.getenv("SSMS_SQLITE_PATH", str(DEFAULT_DB_PATH))
    return Path(p)


def _connect_timeout_sec() -> float:
    """Seconds to wait on connect when another process holds the DB (e.g. DB Browser). Override with SSMS_SQLITE_TIMEOUT."""
    try:
        return max(5.0, float(os.getenv("SSMS_SQLITE_TIMEOUT", "30")))
    except ValueError:
        return 30.0


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=_connect_timeout_sec())
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        # Wait up to 30s when DB is locked by another app (GUI tools often hold write locks).
        conn.execute("PRAGMA busy_timeout=30000")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        course TEXT,
        year INTEGER,
        status TEXT DEFAULT 'active',
        attendance_rate INTEGER DEFAULT 0,
        risk_level TEXT DEFAULT 'low',
        gpa REAL DEFAULT 0.0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin','lecturer','student')),
        student_row_id INTEGER REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS class_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_code TEXT NOT NULL,
        module_name TEXT,
        session_type TEXT,
        session_name TEXT NOT NULL,
        session_date TEXT NOT NULL,
        session_time TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_row_id INTEGER NOT NULL REFERENCES students(id),
        session_id INTEGER REFERENCES class_sessions(id),
        module_code TEXT,
        session_label TEXT,
        check_in_time TEXT NOT NULL,
        status TEXT NOT NULL,
        emotion TEXT,
        emotion_confidence REAL
    );

    CREATE TABLE IF NOT EXISTS emotion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_row_id INTEGER NOT NULL REFERENCES students(id),
        logged_at TEXT NOT NULL,
        context TEXT,
        emotion TEXT,
        confidence REAL
    );

    CREATE TABLE IF NOT EXISTS retention_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_row_id INTEGER NOT NULL REFERENCES students(id),
        severity TEXT,
        message TEXT,
        resolved INTEGER DEFAULT 0,
        resolution_note TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS interventions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_code TEXT NOT NULL,
        type TEXT,
        severity TEXT,
        description TEXT,
        action_taken TEXT,
        assigned_to TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS fee_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_row_id INTEGER NOT NULL REFERENCES students(id),
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        due_date TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_row_id INTEGER NOT NULL REFERENCES students(id),
        fee_item_id INTEGER REFERENCES fee_items(id),
        amount REAL NOT NULL,
        method TEXT,
        reference TEXT,
        paid_at TEXT DEFAULT (datetime('now'))
    );
    """
    with get_connection() as conn:
        conn.executescript(schema)
        _migrate_users_columns(conn)
        _migrate_students_department_legacy(conn)
        _migrate_normalize_esu_emails(conn)
        _repair_admin_account(conn)
        _upgrade_seeded_passwords_to_current_seed(conn)
        _update_admin_name(conn)


def _repair_admin_account(conn: sqlite3.Connection) -> None:
    """Ensure an admin row exists for ADMIN_LOGIN_EMAIL and migrate legacy demo passwords."""
    from auth_util import hash_password, verify_password
    from branding import ADMIN_LOGIN_EMAIL

    # Lazy import avoids circular import at module load (seed imports database).
    from seed import SEED_PASSWORD_ADMIN

    n_admin = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'admin'").fetchone()["c"]
    if int(n_admin) == 0:
        conn.execute(
            """INSERT INTO users (email, password_hash, role, student_row_id, approved, name)
               VALUES (?,?,?,?,1,?)""",
            (ADMIN_LOGIN_EMAIL, hash_password(SEED_PASSWORD_ADMIN), "admin", None, "Morgan Ellis"),
        )
        return

    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE lower(email) = lower(?) AND role = 'admin'",
        (ADMIN_LOGIN_EMAIL,),
    ).fetchone()
    if row is None:
        return
    h = row["password_hash"]
    for legacy in ("demo123", "admin123"):
        if verify_password(legacy, h):
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(SEED_PASSWORD_ADMIN), row["id"]),
            )
            return


def _upgrade_seeded_passwords_to_current_seed(conn: sqlite3.Connection) -> None:
    """
    If demo accounts still use an older seed password hash, re-hash to match seed.py.
    Lets you change SEED_PASSWORD_* without deleting ssms.db (only for known demo emails).
    """
    from auth_util import hash_password, verify_password
    from seed import (
        SEED_PASSWORD_ADMIN,
        SEED_PASSWORD_LECTURER,
        SEED_PASSWORD_STUDENT_EMMA,
        SEED_PASSWORD_STUDENT_JOHN,
    )
    from branding import ADMIN_LOGIN_EMAIL

    # (email, role, canonical plain password, previous passwords we may have shipped)
    accounts: list[tuple[str, str, str, tuple[str, ...]]] = [
        (
            ADMIN_LOGIN_EMAIL,
            "admin",
            SEED_PASSWORD_ADMIN,
            ("demo123", "admin123", "RiverCampus@Admin2026"),
        ),
        (
            "dr.sarah@university.esu",
            "lecturer",
            SEED_PASSWORD_LECTURER,
            ("sarah123", "JohnsonLectures#9", "demo123"),
        ),
        (
            "john.smith@university.esu",
            "student",
            SEED_PASSWORD_STUDENT_JOHN,
            ("john123", "SmithHallway!2026", "demo123"),
        ),
        (
            "emma.j@university.esu",
            "student",
            SEED_PASSWORD_STUDENT_EMMA,
            ("emma123", "EmmaLibrary@Study88", "demo123"),
        ),
    ]

    for email, role, canonical, legacy_plain in accounts:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE lower(email) = lower(?) AND role = ?",
            (email, role),
        ).fetchone()
        if row is None:
            continue
        h = row["password_hash"]
        if verify_password(canonical, h):
            continue
        for old in legacy_plain:
            if verify_password(old, h):
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (hash_password(canonical), row["id"]),
                )
                break


def _migrate_users_columns(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "approved" not in cols:
        conn.execute(
            "ALTER TABLE users ADD COLUMN approved INTEGER NOT NULL DEFAULT 1"
        )
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "name" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN name TEXT")


def _migrate_students_department_legacy(conn: sqlite3.Connection) -> None:
    """Older DBs had a `department` column; drop it when SQLite supports DROP COLUMN (3.35+)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(students)").fetchall()}
    if "department" not in cols:
        return
    try:
        conn.execute("ALTER TABLE students DROP COLUMN department")
    except sqlite3.OperationalError:
        # Older SQLite: column may remain unused; INSERTs omit it (stored as NULL).
        pass


def _migrate_normalize_esu_emails(conn: sqlite3.Connection) -> None:
    """Map legacy @university.ac.uk addresses to @university.esu where present."""
    for table, col in (("students", "email"), ("users", "email")):
        try:
            conn.execute(
                f"""
                UPDATE {table}
                SET {col} = REPLACE({col}, '@university.ac.uk', '@university.esu')
                WHERE {col} LIKE '%@university.ac.uk'
                """
            )
        except sqlite3.OperationalError:
            pass


def _update_admin_name(conn: sqlite3.Connection) -> None:
    from branding import ADMIN_LOGIN_EMAIL
    conn.execute(
        "UPDATE users SET name = 'Ahamed' WHERE lower(email) = lower(?) AND role = 'admin'",
        (ADMIN_LOGIN_EMAIL,),
    )


def table_counts(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    return int(row["c"]) if row else 0
