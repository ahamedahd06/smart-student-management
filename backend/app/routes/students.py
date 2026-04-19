from datetime import datetime, timezone

import pymongo.errors
from flask import Blueprint, current_app, request

from app.routes.middleware import jwt_required, role_required
from app.services.student_service import get_student, list_students, student_to_api
from app.services.auth_service import hash_password
from app.extensions import mongo
from app.utils.responses import err, ok

students_bp = Blueprint("students", __name__)


@students_bp.post("/register")
def register_student():
    """
    Public student self-registration.
    Creates both `students` profile and linked `users` login account.
    Registered before `/<student_id>` so the path `/register` is never captured as an id.
    """
    data = request.get_json(force=True, silent=True) or {}
    required = ["name", "email", "password", "studentId", "department", "year"]
    missing = [k for k in required if not data.get(k) and data.get(k) != 0]
    if missing:
        return err(f"Missing required fields: {', '.join(missing)}", 400)

    email = str(data["email"]).strip().lower()
    student_id_text = str(data["studentId"]).strip().upper()
    internal_id: str | None = None

    try:
        if mongo.db.users.find_one({"email": email}):
            return err("Email already registered", 409)
        if mongo.db.students.find_one({"studentId": student_id_text}):
            return err("Student ID already exists", 409)

        max_id = 0
        for row in mongo.db.students.find({}, {"_id": 1}):
            try:
                max_id = max(max_id, int(str(row["_id"])))
            except ValueError:
                continue
        internal_id = str(max_id + 1)

        try:
            year = int(data["year"])
        except (TypeError, ValueError):
            return err("Year must be a number between 1 and 8", 400)
        if year < 1 or year > 8:
            return err("Year must be between 1 and 8", 400)

        student_doc = {
            "_id": internal_id,
            "name": str(data["name"]).strip(),
            "email": email,
            "studentId": student_id_text,
            "department": str(data["department"]).strip(),
            "year": year,
            "enrollmentDate": str(
                data.get("enrollmentDate") or datetime.now(timezone.utc).date().isoformat()
            ),
            "gpa": float(data.get("gpa") or 0.0),
            "attendanceRate": int(data.get("attendanceRate") or 0),
            "riskLevel": str(data.get("riskLevel") or "low"),
            "isActive": True,
            "createdAt": datetime.now(timezone.utc),
        }
        mongo.db.students.insert_one(student_doc)

        user_doc = {
            "_id": f"usr-stu-{internal_id}",
            "name": student_doc["name"],
            "email": email,
            "password_hash": hash_password(str(data["password"])),
            "role": "student",
            "student_ref": internal_id,
            "isActive": True,
            "createdAt": datetime.now(timezone.utc),
        }
        mongo.db.users.insert_one(user_doc)
        return ok({"student": student_to_api(student_doc), "status": "registered"}, 201)
    except pymongo.errors.DuplicateKeyError:
        if internal_id:
            try:
                mongo.db.students.delete_one({"_id": internal_id})
            except Exception:
                pass
        return err("Email or internal id already exists. Try another Student ID or contact admin.", 409)
    except pymongo.errors.ServerSelectionTimeoutError:
        return err(
            "Cannot connect to MongoDB. Start MongoDB and check MONGODB_URI in backend/.env.",
            503,
        )
    except pymongo.errors.PyMongoError:
        current_app.logger.exception("register_student")
        if internal_id:
            try:
                mongo.db.students.delete_one({"_id": internal_id})
            except Exception:
                pass
        return err("Database error while registering. Is MongoDB running?", 503)


@students_bp.get("/")
@jwt_required
@role_required("admin", "lecturer")
def list_all():
    include_inactive = request.args.get("includeInactive", "0") == "1"
    docs = list_students(include_inactive=include_inactive)
    return ok({"students": [student_to_api(d) for d in docs]})


@students_bp.get("/<student_id>")
@jwt_required
@role_required("admin", "lecturer")
def one(student_id: str):
    doc = get_student(student_id)
    if not doc:
        return err("Not found", 404)
    return ok({"student": student_to_api(doc)})


@students_bp.patch("/<student_id>")
@jwt_required
@role_required("admin")
def update_student(student_id: str):
    doc = get_student(student_id)
    if not doc:
        return err("Student not found", 404)

    data = request.get_json(force=True, silent=True) or {}
    allowed = {
        "name",
        "email",
        "department",
        "year",
        "enrollmentDate",
        "gpa",
        "attendanceRate",
        "riskLevel",
    }
    patch = {k: v for k, v in data.items() if k in allowed}
    if not patch:
        return err("No valid fields provided", 400)

    if "email" in patch:
        patch["email"] = str(patch["email"]).strip().lower()
    if "year" in patch:
        patch["year"] = int(patch["year"])
    if "gpa" in patch:
        patch["gpa"] = float(patch["gpa"])
    if "attendanceRate" in patch:
        patch["attendanceRate"] = int(patch["attendanceRate"])

    if patch.get("gpa") is not None and not (0 <= patch["gpa"] <= 4.0):
        return err("GPA must be between 0 and 4.0", 400)
    if patch.get("year") is not None and not (1 <= patch["year"] <= 8):
        return err("Year must be between 1 and 8", 400)
    if patch.get("attendanceRate") is not None and not (0 <= patch["attendanceRate"] <= 100):
        return err("Attendance rate must be between 0 and 100", 400)

    # Keep linked user email in sync for student accounts.
    if "email" in patch:
        mongo.db.users.update_many({"student_ref": student_id}, {"$set": {"email": patch["email"]}})

    patch["updatedAt"] = datetime.now(timezone.utc)
    mongo.db.students.update_one({"_id": student_id}, {"$set": patch})
    updated = mongo.db.students.find_one({"_id": student_id})
    return ok({"student": student_to_api(updated)})


@students_bp.delete("/<student_id>")
@jwt_required
@role_required("admin")
def delete_student(student_id: str):
    doc = get_student(student_id)
    if not doc:
        return err("Student not found", 404)

    # Soft delete for auditability.
    now = datetime.now(timezone.utc)
    mongo.db.students.update_one(
        {"_id": student_id},
        {"$set": {"isActive": False, "deletedAt": now, "updatedAt": now}},
    )
    mongo.db.users.update_many(
        {"student_ref": student_id},
        {"$set": {"isActive": False, "updatedAt": now}},
    )
    return ok({"status": "deactivated", "studentId": student_id})


@students_bp.post("/<student_id>/reactivate")
@jwt_required
@role_required("admin")
def reactivate_student(student_id: str):
    doc = get_student(student_id)
    if not doc:
        return err("Student not found", 404)
    now = datetime.now(timezone.utc)
    mongo.db.students.update_one(
        {"_id": student_id},
        {"$set": {"isActive": True, "updatedAt": now}, "$unset": {"deletedAt": ""}},
    )
    mongo.db.users.update_many(
        {"student_ref": student_id},
        {"$set": {"isActive": True, "updatedAt": now}},
    )
    return ok({"status": "reactivated", "studentId": student_id})


@students_bp.post("/<student_id>/reset-password")
@jwt_required
@role_required("admin")
def reset_student_password(student_id: str):
    data = request.get_json(force=True, silent=True) or {}
    password = data.get("password")
    if not password or len(str(password)) < 6:
        return err("Password must be at least 6 characters", 400)
    res = mongo.db.users.update_many(
        {"student_ref": student_id},
        {"$set": {"password_hash": hash_password(str(password))}},
    )
    if res.matched_count == 0:
        return err("Linked student account not found", 404)
    return ok({"status": "password_reset", "studentId": student_id})
