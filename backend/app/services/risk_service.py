"""
Risk rules aligned with frontend tooltips in StudentList / RiskCriteriaCard:
- high: attendance < 65 OR negative emotion share (sad+angry) > 60% in recent window
- medium: attendance < 80 OR negative share > 40%
- else low
"""

from datetime import datetime, timedelta, timezone

from app.extensions import mongo

NEGATIVE = {"sad", "angry"}


def _recent_emotions(student_id: str, days: int = 14) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return list(
        mongo.db.emotion_records.find(
            {"student_id": student_id, "timestamp": {"$gte": cutoff}}
        ).sort("timestamp", -1)
    )


def _attendance_rate(student_id: str, last_n: int = 40) -> int:
    records = list(
        mongo.db.attendance_records.find({"student_id": student_id})
        .sort("timestamp", -1)
        .limit(last_n)
    )
    if not records:
        # fall back to stored field
        s = mongo.db.students.find_one({"_id": student_id})
        return int(s.get("attendanceRate", 0)) if s else 0
    present = sum(1 for r in records if r.get("status") == "present")
    return int(round(100 * present / len(records)))


def compute_negative_share(emotions: list[dict]) -> float:
    if not emotions:
        return 0.0
    neg = sum(1 for e in emotions if e.get("emotion") in NEGATIVE)
    return 100.0 * neg / len(emotions)


def compute_risk_level(attendance_rate: int, negative_share: float) -> str:
    if attendance_rate < 65 or negative_share > 60:
        return "high"
    if attendance_rate < 80 or negative_share > 40:
        return "medium"
    return "low"


def recompute_for_student(student_id: str) -> tuple[int, str]:
    emotions = _recent_emotions(student_id)
    neg_share = compute_negative_share(emotions)
    att = _attendance_rate(student_id)
    risk = compute_risk_level(att, neg_share)
    return att, risk


def maybe_generate_alerts(student_id: str) -> None:
    """Create or update alerts when risk is elevated (explainable rules)."""
    att, risk = recompute_for_student(student_id)
    student = mongo.db.students.find_one({"_id": student_id})
    if not student:
        return

    existing = mongo.db.retention_alerts.find_one(
        {"student_id": student_id, "resolved": False, "alertType": "combined"}
    )
    if risk == "high" and not existing:
        msg_parts = []
        if att < 65:
            msg_parts.append(f"Low attendance ({att}%)")
        neg_share = compute_negative_share(_recent_emotions(student_id))
        if neg_share > 40:
            msg_parts.append("frequent sad/angry detections recently")
        message = " and ".join(msg_parts) or "Multiple risk indicators"
        mongo.db.retention_alerts.insert_one(
            {
                "student_id": student_id,
                "alertType": "combined",
                "severity": "high",
                "message": message.capitalize(),
                "timestamp": datetime.now(timezone.utc),
                "resolved": False,
            }
        )
    elif risk == "medium":
        emo = mongo.db.retention_alerts.find_one(
            {"student_id": student_id, "resolved": False, "alertType": "emotional"}
        )
        neg_share = compute_negative_share(_recent_emotions(student_id))
        if neg_share > 35 and not emo:
            mongo.db.retention_alerts.insert_one(
                {
                    "student_id": student_id,
                    "alertType": "emotional",
                    "severity": "medium",
                    "message": "Elevated negative emotions (sad/angry) in recent check-ins",
                    "timestamp": datetime.now(timezone.utc),
                    "resolved": False,
                }
            )
