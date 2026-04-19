"""Self-registration: students (immediate) and lecturers (pending admin approval)."""
from __future__ import annotations

import re
import sqlite3
from datetime import date, timedelta

from auth_util import hash_password
from database import get_connection

# Optional: restrict institutional email (set SSMS_REQUIRE_ESU_EMAIL=1 in environment)
import os

REQUIRE_ESU = os.getenv("SSMS_REQUIRE_ESU_EMAIL", "0") == "1"
ESU_SUFFIX = "@university.esu"

# Initial outstanding balance for every newly self-registered student (LKR).
NEW_STUDENT_OUTSTANDING_AMOUNT = 50_000.0
NEW_STUDENT_OUTSTANDING_DESC = "Outstanding payment — new student registration"
NEW_STUDENT_OUTSTANDING_DUE_DAYS = 90


def _email_ok_for_institution(email: str) -> tuple[bool, str]:
    e = email.strip().lower()
    if REQUIRE_ESU and not e.endswith(ESU_SUFFIX):
        return False, f"Email must end with {ESU_SUFFIX}"
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e):
        return False, "Invalid email format."
    return True, e


def register_new_student(
    *,
    name: str,
    student_code: str,
    email: str,
    password: str,
    course: str,
    year: int,
) -> tuple[bool, str]:
    ok, msg = _email_ok_for_institution(email)
    if not ok:
        return False, msg
    email = msg
    code = student_code.strip().upper()
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not code or not name.strip():
        return False, "Name and student ID are required."

    try:
        with get_connection() as conn:
            if conn.execute("SELECT 1 FROM users WHERE lower(email)=?", (email,)).fetchone():
                return False, "That email is already registered."
            if conn.execute("SELECT 1 FROM students WHERE student_code=?", (code,)).fetchone():
                return False, "That student ID is already taken."
            conn.execute(
                """INSERT INTO students (student_code, name, email, course, year, status)
                   VALUES (?,?,?,?,?,?)""",
                (code, name.strip(), email, course.strip(), int(year), "active"),
            )
            sid = conn.execute("SELECT id FROM students WHERE student_code=?", (code,)).fetchone()["id"]
            conn.execute(
                """INSERT INTO users (email, password_hash, role, student_row_id, approved, name)
                   VALUES (?,?,?,?,1,?)""",
                (email, hash_password(password), "student", sid, name.strip()),
            )
            due = (date.today() + timedelta(days=NEW_STUDENT_OUTSTANDING_DUE_DAYS)).isoformat()
            conn.execute(
                """INSERT INTO fee_items (student_row_id, description, amount, due_date)
                   VALUES (?,?,?,?)""",
                (sid, NEW_STUDENT_OUTSTANDING_DESC, NEW_STUDENT_OUTSTANDING_AMOUNT, due),
            )
    except sqlite3.IntegrityError as e:
        return False, f"Could not register: {e}"
    return (
        True,
        "Registration successful. You can sign in as Student. "
        f"An outstanding fee of LKR {NEW_STUDENT_OUTSTANDING_AMOUNT:,.0f} has been added to your account.",
    )


def register_new_lecturer(*, name: str, email: str, password: str) -> tuple[bool, str]:
    ok, msg = _email_ok_for_institution(email)
    if not ok:
        return False, msg
    email = msg
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not name.strip():
        return False, "Name is required."

    with get_connection() as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email)=?", (email,)).fetchone():
            return False, "That email is already registered."
        # Lecturer accounts start unapproved (admin must approve)
        conn.execute(
            """INSERT INTO users (email, password_hash, role, student_row_id, approved, name)
               VALUES (?,?,?,?,0,?)""",
            (email, hash_password(password), "lecturer", None, name.strip()),
        )
    return (
        True,
        "Request submitted. An administrator must approve your account before you can sign in as Lecturer.",
    )


def list_pending_lecturers(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT id, email, name FROM users
           WHERE role='lecturer' AND IFNULL(approved,1)=0
           ORDER BY id"""
    ).fetchall()


def approve_lecturer(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE users SET approved=1 WHERE id=? AND role='lecturer'", (user_id,))


def reject_lecturer(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id=? AND role='lecturer' AND IFNULL(approved,1)=0", (user_id,))
