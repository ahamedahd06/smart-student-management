from flask import Blueprint, g

from app.routes.middleware import jwt_required, role_required
from app.services import analytics_service
from app.utils.responses import err, ok

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/summary")
@jwt_required
@role_required("admin", "lecturer")
def summary():
    return ok(analytics_service.summary_metrics())


@analytics_bp.get("/emotion-trends")
@jwt_required
@role_required("admin", "lecturer")
def emotion_trends():
    return ok({"series": analytics_service.admin_emotion_trends()})


@analytics_bp.get("/weekly-attendance")
@jwt_required
@role_required("admin", "lecturer")
def weekly():
    return ok({"series": analytics_service.weekly_attendance_admin()})


@analytics_bp.get("/student/emotion-trend")
@jwt_required
def student_emotion():
    if g.current_user.get("role") != "student":
        return err("Forbidden", 403)
    ref = g.current_user.get("student_ref")
    if not ref:
        return err("Student profile not linked", 400)
    return ok({"series": analytics_service.student_emotion_trend(ref)})


@analytics_bp.get("/student/weekly-attendance")
@jwt_required
def student_weekly():
    if g.current_user.get("role") != "student":
        return err("Forbidden", 403)
    ref = g.current_user.get("student_ref")
    if not ref:
        return err("Student profile not linked", 400)
    return ok({"series": analytics_service.student_weekly_attendance(ref)})


@analytics_bp.get("/monitor-stats")
@jwt_required
@role_required("admin", "lecturer")
def monitor():
    return ok(analytics_service.monitor_stats_today())
