from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, g, request

from app.extensions import mongo
from app.routes.middleware import jwt_required, role_required
from app.utils.responses import err, ok

alerts_bp = Blueprint("alerts", __name__)


def _serialize_alert(doc: dict) -> dict:
    ts: datetime = doc["timestamp"]
    res = doc.get("resolution")
    out = {
        "id": str(doc["_id"]),
        "studentId": doc.get("student_id"),
        "alertType": doc.get("alertType"),
        "severity": doc.get("severity"),
        "message": doc.get("message"),
        "timestamp": ts.isoformat(),
        "resolved": bool(doc.get("resolved")),
    }
    if res:
        out["resolution"] = res
    return out


@alerts_bp.get("/")
@jwt_required
def list_alerts():
    role = g.current_user.get("role")
    q: dict = {}
    if role == "student":
        ref = g.current_user.get("student_ref")
        if not ref:
            return err("Student profile not linked", 400)
        q["student_id"] = ref
    cur = mongo.db.retention_alerts.find(q).sort("timestamp", -1)
    return ok({"alerts": [_serialize_alert(d) for d in cur]})


@alerts_bp.patch("/<alert_id>/resolve")
@jwt_required
@role_required("admin", "lecturer")
def resolve(alert_id: str):
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("actionTaken") or data.get("action_taken")
    notes = data.get("notes")
    follow = data.get("followUpDate") or data.get("follow_up_date")
    if not action or not notes:
        return err("actionTaken and notes are required", 400)

    try:
        filt = {"_id": ObjectId(alert_id)}
    except Exception:
        filt = {"_id": alert_id}

    doc = mongo.db.retention_alerts.find_one(filt)
    if not doc:
        return err("Alert not found", 404)

    resolution = {
        "action_taken": action,
        "notes": notes,
        "follow_up_date": follow,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }
    mongo.db.retention_alerts.update_one(
        filt,
        {"$set": {"resolved": True, "resolution": resolution}},
    )
    updated = mongo.db.retention_alerts.find_one(filt)
    return ok({"alert": _serialize_alert(updated)})
