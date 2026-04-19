from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from app.extensions import mongo


def summary_metrics() -> dict[str, Any]:
    students = list(mongo.db.students.find({}))
    if not students:
        return {
            "averageAttendance": 0,
            "averageGpa": 0.0,
            "atRiskPercent": 0,
        }
    avg_att = sum(int(s.get("attendanceRate", 0)) for s in students) / len(students)
    avg_gpa = sum(float(s.get("gpa", 0)) for s in students) / len(students)
    at_risk = sum(1 for s in students if s.get("riskLevel") in ("medium", "high"))
    return {
        "averageAttendance": int(round(avg_att)),
        "averageGpa": round(avg_gpa, 2),
        "atRiskPercent": int(round(100 * at_risk / len(students))),
    }


def admin_emotion_trends(days: int = 8) -> list[dict[str, Any]]:
    """Aggregate emotion counts per calendar day for admin chart (4 classes)."""
    start = datetime.now(timezone.utc) - timedelta(days=days)
    docs = mongo.db.emotion_records.find({"timestamp": {"$gte": start}}).sort("timestamp", 1)
    by_date: dict[str, dict[str, int]] = defaultdict(
        lambda: {"happy": 0, "sad": 0, "neutral": 0, "angry": 0}
    )
    for row in docs:
        ts: datetime = row["timestamp"]
        d = ts.strftime("%m/%d")
        emo = row.get("emotion", "neutral")
        if emo in by_date[d]:
            by_date[d][emo] += 1
    items = sorted(by_date.items(), key=lambda x: x[0])
    return [{"date": k, **v} for k, v in items]


def weekly_attendance_admin() -> list[dict[str, Any]]:
    """Last 4 weeks present ratio across all students (simplified for demo)."""
    now = datetime.now(timezone.utc)
    weeks = []
    for i in range(4, 0, -1):
        start = now - timedelta(weeks=i)
        end = now - timedelta(weeks=i - 1)
        total = mongo.db.attendance_records.count_documents(
            {"timestamp": {"$gte": start, "$lt": end}}
        )
        # treat each record as one slot; cap display at 100 for chart scale
        pct = min(100, total * 2) if total else 0
        weeks.append({"week": f"Week {5 - i}", "attendance": pct})
    return weeks


def student_emotion_trend(student_id: str, days: int = 7) -> list[dict[str, Any]]:
    start = datetime.now(timezone.utc) - timedelta(days=days)
    cur = mongo.db.emotion_records.find(
        {"student_id": student_id, "timestamp": {"$gte": start}}
    ).sort("timestamp", 1)
    by_date: dict[str, dict[str, int]] = defaultdict(
        lambda: {"happy": 0, "sad": 0, "neutral": 0, "angry": 0}
    )
    for r in cur:
        d = r["timestamp"].strftime("%m/%d")
        emo = r.get("emotion", "neutral")
        if emo in by_date[d]:
            by_date[d][emo] += 1
    return [{"date": k, **vals} for k, vals in sorted(by_date.items(), key=lambda x: x[0])]


def student_weekly_attendance(student_id: str) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    out = []
    for i in range(4, 0, -1):
        start = now - timedelta(weeks=i)
        end = now - timedelta(weeks=i - 1)
        n = mongo.db.attendance_records.count_documents(
            {"student_id": student_id, "timestamp": {"$gte": start, "$lt": end}}
        )
        pct = min(100, n * 10)
        out.append({"week": f"Week {5 - i}", "attendance": pct})
    return out


def monitor_stats_today() -> dict[str, Any]:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    total = mongo.db.attendance_records.count_documents({"timestamp": {"$gte": start}})
    emos = list(
        mongo.db.emotion_records.find({"timestamp": {"$gte": start}})
    )
    if not emos:
        return {
            "checkInsToday": total,
            "positivePercent": 0,
            "neutralPercent": 0,
            "negativePercent": 0,
        }
    pos = sum(1 for e in emos if e.get("emotion") == "happy")
    neu = sum(1 for e in emos if e.get("emotion") == "neutral")
    neg = sum(1 for e in emos if e.get("emotion") in ("sad", "angry"))
    t = len(emos)
    return {
        "checkInsToday": max(total, t),
        "positivePercent": int(round(100 * pos / t)),
        "neutralPercent": int(round(100 * neu / t)),
        "negativePercent": int(round(100 * neg / t)),
    }
