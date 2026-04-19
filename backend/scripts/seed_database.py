"""
Seed MongoDB with demo users/students/alerts matching the original frontend mock data.
Run from repo root: python -m scripts.seed_database  (from backend folder: python scripts/seed_database.py)
"""
from __future__ import annotations

import os
import sys

from datetime import datetime, timezone

import bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def main():
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "smart_student_db")
    client = MongoClient(uri)
    db = client[db_name]

    for name in (
        "users",
        "students",
        "retention_alerts",
        "attendance_records",
        "emotion_records",
    ):
        db[name].delete_many({})

    demo_pw = _hash_password(os.getenv("SEED_DEMO_PASSWORD", "demo123"))

    students = [
        {
            "_id": "1",
            "name": "Emma Johnson",
            "email": "emma.j@university.esu",
            "studentId": "STU001",
            "department": "Computer Science",
            "year": 3,
            "enrollmentDate": "2022-09-01",
            "gpa": 3.8,
            "attendanceRate": 95,
            "riskLevel": "low",
        },
        {
            "_id": "2",
            "name": "Michael Chen",
            "email": "michael.c@university.esu",
            "studentId": "STU002",
            "department": "Engineering",
            "year": 2,
            "enrollmentDate": "2023-09-01",
            "gpa": 3.2,
            "attendanceRate": 78,
            "riskLevel": "medium",
        },
        {
            "_id": "3",
            "name": "Sarah Williams",
            "email": "sarah.w@university.esu",
            "studentId": "STU003",
            "department": "Business",
            "year": 4,
            "enrollmentDate": "2021-09-01",
            "gpa": 2.9,
            "attendanceRate": 65,
            "riskLevel": "high",
        },
        {
            "_id": "4",
            "name": "David Martinez",
            "email": "david.m@university.esu",
            "studentId": "STU004",
            "department": "Computer Science",
            "year": 1,
            "enrollmentDate": "2024-09-01",
            "gpa": 3.9,
            "attendanceRate": 92,
            "riskLevel": "low",
        },
        {
            "_id": "5",
            "name": "Lisa Anderson",
            "email": "lisa.a@university.esu",
            "studentId": "STU005",
            "department": "Psychology",
            "year": 3,
            "enrollmentDate": "2022-09-01",
            "gpa": 3.1,
            "attendanceRate": 70,
            "riskLevel": "medium",
        },
    ]
    db.students.insert_many(students)

    users = [
        {
            "_id": "usr-admin",
            "name": "Dr. Admin User",
            "email": "admin@university.esu",
            "password_hash": demo_pw,
            "role": "admin",
        },
        {
            "_id": "usr-lec",
            "name": "Prof. John Smith",
            "email": "j.smith@university.esu",
            "password_hash": demo_pw,
            "role": "lecturer",
        },
        {
            "_id": "usr-stu-1",
            "name": "Emma Johnson",
            "email": "emma.j@university.esu",
            "password_hash": demo_pw,
            "role": "student",
            "student_ref": "1",
        },
        {
            "_id": "usr-stu-3",
            "name": "Sarah Williams",
            "email": "sarah.w@university.esu",
            "password_hash": demo_pw,
            "role": "student",
            "student_ref": "3",
        },
    ]
    db.users.insert_many(users)

    alerts = [
        {
            "student_id": "3",
            "alertType": "combined",
            "severity": "high",
            "message": "Low attendance (65%) and consistently stressed emotional state detected",
            "timestamp": datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
            "resolved": False,
        },
        {
            "student_id": "2",
            "alertType": "emotional",
            "severity": "medium",
            "message": "Frequent negative emotions detected in technical classes",
            "timestamp": datetime(2026, 1, 27, 10, 30, tzinfo=timezone.utc),
            "resolved": False,
        },
        {
            "student_id": "5",
            "alertType": "attendance",
            "severity": "medium",
            "message": "Attendance rate declining over past 3 weeks",
            "timestamp": datetime(2026, 1, 26, 16, 0, tzinfo=timezone.utc),
            "resolved": False,
        },
    ]
    db.retention_alerts.insert_many(alerts)

    print(f"Seeded database '{db_name}' on {uri}")
    print("Demo password for all seeded accounts:", os.getenv("SEED_DEMO_PASSWORD", "demo123"))


if __name__ == "__main__":
    main()
