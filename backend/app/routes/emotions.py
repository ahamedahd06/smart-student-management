from datetime import datetime

from flask import Blueprint, g

from app.extensions import mongo
from app.routes.middleware import jwt_required
from app.utils.responses import err, ok

emotions_bp = Blueprint("emotions", __name__)


def _serialize_emotion(doc: dict) -> dict:
    ts: datetime = doc["timestamp"]
    conf = float(doc.get("confidence", 0))
    return {
        "id": str(doc["_id"]),
        "studentId": doc.get("student_id"),
        "timestamp": ts.isoformat(),
        "emotion": doc.get("emotion"),
        "confidence": conf,
        "confidencePercent": int(round(conf * 100)) if conf <= 1.0 else int(round(conf)),
        "location": doc.get("location", ""),
    }


@emotions_bp.get("/my")
@jwt_required
def my_emotions():
    if g.current_user.get("role") != "student":
        return err("Forbidden", 403)
    ref = g.current_user.get("student_ref")
    if not ref:
        return err("Student profile not linked", 400)
    cur = (
        mongo.db.emotion_records.find({"student_id": ref})
        .sort("timestamp", -1)
        .limit(200)
    )
    return ok({"records": [_serialize_emotion(d) for d in cur]})
