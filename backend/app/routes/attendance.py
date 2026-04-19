from flask import Blueprint, g, request

from app.extensions import mongo
from app.routes.middleware import jwt_required, role_required
from app.services import attendance_service
from app.utils.responses import err, ok

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.post("/check-in")
@jwt_required
def check_in():
    if g.current_user.get("role") != "student":
        return err("Only students can check in from this endpoint", 403)
    student_ref = g.current_user.get("student_ref")
    if not student_ref:
        return err("Student profile not linked to user", 400)

    if "image" not in request.files:
        return err("Image file required (field name: image)", 400)
    module = request.form.get("module") or request.form.get("class")
    session = request.form.get("session")
    session_date = request.form.get("date")
    location = request.form.get("location") or "Campus"
    if not module or not session or not session_date:
        return err("module, session, and date are required", 400)

    f = request.files["image"]
    image_bytes = f.read()
    if not image_bytes:
        return err("Empty image", 400)

    stu = mongo.db.students.find_one({"_id": student_ref})
    if not stu:
        return err("Student record missing", 404)

    encoding = stu.get("face_encoding")

    try:
        result = attendance_service.process_check_in(
            student_id=student_ref,
            image_bytes=image_bytes,
            module_code=module,
            session=session,
            session_date=session_date,
            location=location,
            known_encoding=encoding,
        )
    except PermissionError as e:
        return err(str(e), 403)
    except RuntimeError as e:
        return err(str(e), 503)

    return ok(result, 201)


@attendance_bp.get("/me")
@jwt_required
def my_records():
    if g.current_user.get("role") != "student":
        return err("Forbidden", 403)
    student_ref = g.current_user.get("student_ref")
    if not student_ref:
        return err("Student profile not linked", 400)
    rows = attendance_service.list_my_attendance(student_ref)
    return ok({"records": rows})


@attendance_bp.get("/me/status")
@jwt_required
def my_status():
    if g.current_user.get("role") != "student":
        return err("Forbidden", 403)
    student_ref = g.current_user.get("student_ref")
    if not student_ref:
        return err("Student profile not linked", 400)
    summary = attendance_service.check_in_status_summary(student_ref)
    return ok(summary)


@attendance_bp.get("/recent")
@jwt_required
@role_required("admin", "lecturer")
def recent():
    rows = attendance_service.list_recent_checkins()
    return ok({"recent": rows})
