"""Seed sample students, sessions, and evaluation accounts when the database is empty."""
from __future__ import annotations

import sqlite3

from branding import ADMIN_LOGIN_EMAIL
from database import get_connection, init_db, table_counts
from auth_util import hash_password

# Demo passwords: lowercase first name + "123" (e.g. admin123, sarah123).
# Kept in sync with README. Change in production.
SEED_PASSWORD_ADMIN = "admin123"
SEED_PASSWORD_LECTURER = "sarah123"
SEED_PASSWORD_STUDENT_JOHN = "john123"
SEED_PASSWORD_STUDENT_EMMA = "emma123"


def seed_if_empty() -> None:
    init_db()
    with get_connection() as conn:
        if table_counts(conn) > 0:
            return
        _seed(conn)


def _seed(conn: sqlite3.Connection) -> None:
    pw_admin = hash_password(SEED_PASSWORD_ADMIN)
    pw_lecturer = hash_password(SEED_PASSWORD_LECTURER)
    pw_john = hash_password(SEED_PASSWORD_STUDENT_JOHN)
    pw_emma = hash_password(SEED_PASSWORD_STUDENT_EMMA)

    students = [
        (
            "S001",
            "John Smith",
            "john.smith@university.esu",
            "Computer Science",
            2,
            "active",
            92,
            "low",
            3.4,
        ),
        (
            "S002",
            "Emma Johnson",
            "emma.j@university.esu",
            "Software Engineering",
            3,
            "active",
            95,
            "low",
            3.8,
        ),
        (
            "S003",
            "Michael Brown",
            "michael.brown@university.esu",
            "Data Science",
            2,
            "active",
            78,
            "medium",
            3.2,
        ),
        (
            "S004",
            "Sarah Davis",
            "sarah.d@university.esu",
            "Cyber Security",
            4,
            "active",
            65,
            "high",
            2.9,
        ),
        (
            "S005",
            "James Wilson",
            "james.w@university.esu",
            "Fashion Design",
            1,
            "active",
            40,
            "high",
            2.1,
        ),
    ]
    conn.executemany(
        """INSERT INTO students (student_code, name, email, course, year, status, attendance_rate, risk_level, gpa)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        students,
    )

    conn.execute(
        """INSERT INTO users (email, password_hash, role, student_row_id, approved, name)
           VALUES (?,?,?,?,1,?)""",
        (ADMIN_LOGIN_EMAIL, pw_admin, "admin", None, "Ahamed"),
    )
    conn.execute(
        """INSERT INTO users (email, password_hash, role, student_row_id, approved, name)
           VALUES (?,?,?,?,1,?)""",
        ("dr.sarah@university.esu", pw_lecturer, "lecturer", None, "Dr. Sarah Johnson"),
    )

    for code, email, pw in [
        ("S001", "john.smith@university.esu", pw_john),
        ("S002", "emma.j@university.esu", pw_emma),
    ]:
        sid = conn.execute(
            "SELECT id FROM students WHERE student_code = ?", (code,)
        ).fetchone()["id"]
        name_row = conn.execute(
            "SELECT name FROM students WHERE student_code = ?", (code,)
        ).fetchone()
        disp = name_row["name"] if name_row else None
        conn.execute(
            """INSERT INTO users (email, password_hash, role, student_row_id, approved, name)
               VALUES (?,?,?,?,1,?)""",
            (email, pw, "student", sid, disp),
        )

    # module_code and module_name are the same human-readable module (no short codes).
    sessions = [
        ("Computer Science", "Computer Science", "Lecture", "Week 3 lecture", "2026-01-29", "09:00"),
        ("Software Engineering", "Software Engineering", "Lab", "Sprint lab", "2026-01-27", "10:00"),
        ("Data Science", "Data Science", "Tutorial", "Statistics clinic", "2026-01-28", "14:00"),
        ("Cyber Security", "Cyber Security", "Lecture", "Network security", "2026-01-26", "11:00"),
        ("Fashion Design", "Fashion Design", "Workshop", "Studio session", "2026-01-25", "13:00"),
    ]
    conn.executemany(
        """INSERT INTO class_sessions (module_code, module_name, session_type, session_name, session_date, session_time)
           VALUES (?,?,?,?,?,?)""",
        sessions,
    )

    sid1 = conn.execute("SELECT id FROM students WHERE student_code='S001'").fetchone()["id"]
    sess1 = conn.execute("SELECT id FROM class_sessions WHERE session_name='Week 3 lecture'").fetchone()["id"]
    conn.execute(
        """INSERT INTO attendance_records
           (student_row_id, session_id, module_code, session_label, check_in_time, status, emotion, emotion_confidence)
           VALUES (?,?,?,?,?,?,?,?)""",
        (sid1, sess1, "Computer Science", "Week 3 lecture", "2026-01-29T09:02:00", "present", "happy", 0.92),
    )

    conn.execute(
        """INSERT INTO emotion_logs (student_row_id, logged_at, context, emotion, confidence)
           VALUES (?,?,?,?,?)""",
        (sid1, "2026-01-29T09:02:00", "Computer Science — Week 3 lecture check-in", "happy", 0.92),
    )

    conn.execute(
        """INSERT INTO retention_alerts (student_row_id, severity, message, resolved)
           VALUES (?,?,?,?)""",
        (
            conn.execute("SELECT id FROM students WHERE student_code='S005'").fetchone()["id"],
            "critical",
            "Student has missed 6 out of 10 recent sessions",
            0,
        ),
    )

    # --- Seed fee items for demo students ---
    all_students = conn.execute("SELECT id, student_code FROM students").fetchall()
    fee_templates = [
        ("Tuition Fee – Semester 2", 185000.00, "2026-03-01"),
        ("Library & Resources Fee", 12500.00, "2026-02-15"),
        ("Student Union Fee", 5000.00, "2026-02-01"),
    ]
    for stu in all_students:
        for desc, amt, due in fee_templates:
            conn.execute(
                """INSERT INTO fee_items (student_row_id, description, amount, due_date)
                   VALUES (?,?,?,?)""",
                (stu["id"], desc, amt, due),
            )

    # John (S001) paid tuition and library fee
    john_fees = conn.execute(
        "SELECT id, amount FROM fee_items WHERE student_row_id = ? ORDER BY id",
        (sid1,),
    ).fetchall()
    if len(john_fees) >= 2:
        conn.execute(
            """INSERT INTO payments (student_row_id, fee_item_id, amount, method, reference)
               VALUES (?,?,?,?,?)""",
            (sid1, john_fees[0]["id"], john_fees[0]["amount"], "Bank Transfer", "TXN-20260215-001"),
        )
        conn.execute(
            """INSERT INTO payments (student_row_id, fee_item_id, amount, method, reference)
               VALUES (?,?,?,?,?)""",
            (sid1, john_fees[1]["id"], john_fees[1]["amount"], "Card", "TXN-20260218-002"),
        )
