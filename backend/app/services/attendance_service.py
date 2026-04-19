from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.extensions import mongo
from app.ml import face_service
from app.ml.emotion_service import EmotionModelError, predict_emotion_rgb
from app.ml.preprocess import crop_face_rgb, pil_from_bytes
from app.services import risk_service
from app.services.student_service import update_student_metrics


def _insert_emotion(student_id: str, emotion: str, confidence: float, location: str) -> str:
    doc = {
        "student_id": student_id,
        "timestamp": datetime.now(timezone.utc),
        "emotion": emotion,
        "confidence": confidence,
        "location": location,
        "source": "check_in",
    }
    res = mongo.db.emotion_records.insert_one(doc)
    return str(res.inserted_id)


def process_check_in(
    *,
    student_id: str,
    image_bytes: bytes,
    module_code: str,
    session: str,
    session_date: str,
    location: str,
    known_encoding: list[float] | None,
) -> dict[str, Any]:
    if not face_service.verify_same_person(image_bytes, known_encoding):
        raise PermissionError("Face verification failed for this account")

    fr_locs = face_service.locate_largest_face(image_bytes)
    pil = pil_from_bytes(image_bytes)
    if fr_locs:
        face_img = crop_face_rgb(pil, fr_locs)
    else:
        face_img = pil

    try:
        emotion, conf = predict_emotion_rgb(face_img)
    except EmotionModelError as e:
        raise RuntimeError(str(e)) from e

    # allowed 4 classes — clamp unknown labels to neutral for storage consistency
    allowed = {"happy", "sad", "neutral", "angry"}
    if emotion not in allowed:
        emotion = "neutral"

    # Store model confidence as 0..1 for consistent API serialization
    conf_store = conf if conf <= 1.0 else conf / 100.0
    emo_id = _insert_emotion(student_id, emotion, conf_store, location)

    now = datetime.now(timezone.utc)
    att_doc = {
        "student_id": student_id,
        "timestamp": now,
        "checkInMethod": "facial",
        "class": module_code,
        "location": location,
        "session": session,
        "session_date": session_date,
        "status": "present",
        "emotion_id": emo_id,
        "emotion": emotion,
        "emotion_confidence": conf_store,
    }
    res = mongo.db.attendance_records.insert_one(att_doc)

    att, risk = risk_service.recompute_for_student(student_id)
    update_student_metrics(student_id, att, risk)
    risk_service.maybe_generate_alerts(student_id)

    stu = mongo.db.students.find_one({"_id": student_id})
    return {
        "attendanceId": str(res.inserted_id),
        "emotionId": emo_id,
        "studentId": stu.get("studentId") if stu else None,
        "studentName": stu.get("name") if stu else None,
        "emotion": emotion,
        "confidence": round((conf if conf <= 1.0 else conf / 100.0) * 100, 1),
        "recordedAt": now.isoformat(),
    }


def list_my_attendance(student_id: str, limit: int = 100) -> list[dict]:
    cur = (
        mongo.db.attendance_records.find({"student_id": student_id})
        .sort("timestamp", -1)
        .limit(limit)
    )
    out = []
    for r in cur:
        ts: datetime = r["timestamp"]
        out.append(
            {
                "id": str(r["_id"]),
                "date": r.get("session_date") or ts.date().isoformat(),
                "module": r.get("class"),
                "session": r.get("session", ""),
                "time": ts.strftime("%H:%M") if r.get("status") == "present" else "-",
                "status": r.get("status", "present"),
                "timestamp": ts.isoformat(),
            }
        )
    return out


def list_recent_checkins(limit: int = 25) -> list[dict]:
    cur = mongo.db.attendance_records.find({}).sort("timestamp", -1).limit(limit)
    out = []
    for r in cur:
        stu = mongo.db.students.find_one({"_id": r["student_id"]})
        ts: datetime = r["timestamp"]
        label = f"{stu.get('name') if stu else 'Unknown'} - {stu.get('studentId') if stu else ''}"
        out.append({"label": label.strip(), "timestamp": ts.isoformat()})
    return out


def check_in_status_summary(student_id: str, session_date: str | None = None) -> dict[str, Any]:
    """Approximate 'this week' stats for student sidebar in App — uses last 7 days of records."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    records = list(
        mongo.db.attendance_records.find(
            {"student_id": student_id, "timestamp": {"$gte": start}}
        ).sort("timestamp", -1)
    )
    last = records[0]["timestamp"] if records else None
    present = sum(1 for r in records if r.get("status") == "present")
    total = len(records) if records else 1
    rate = int(round(100 * present / total))
    return {
        "lastCheckIn": last.isoformat() if last else None,
        "weekPresent": present,
        "weekTotal": total,
        "weekRatePercent": rate,
    }
