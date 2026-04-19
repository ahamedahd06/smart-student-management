from datetime import datetime, timezone

from flask import Blueprint, g, request

from app.extensions import mongo
from app.routes.middleware import jwt_required
from app.services.auth_service import (
    create_token,
    find_user_by_email,
    hash_password,
    public_user,
    verify_password,
)
from app.services.student_service import student_to_api
from app.utils.responses import err, ok

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role")
    if not email or not password:
        return err("Email and password required", 400)

    user = find_user_by_email(email)
    if not user or not verify_password(password, user.get("password_hash", "")):
        return err("Invalid credentials", 401)
    if user.get("isActive", True) is False:
        return err("Account is deactivated. Contact admin.", 403)
    if user.get("role") == "lecturer" and user.get("approvalStatus", "approved") != "approved":
        return err("Lecturer account is pending admin approval.", 403)
    if role and user.get("role") != role:
        return err("Selected role does not match this account", 403)

    student = None
    if user.get("student_ref"):
        student = mongo.db.students.find_one({"_id": user["student_ref"]})
        if student and student.get("isActive", True) is False:
            return err("Student profile is deactivated. Contact admin.", 403)

    token = create_token(user)
    body = {"token": token, "user": public_user(user, student)}
    if student:
        body["student"] = student_to_api(student)
    return ok(body)


@auth_bp.get("/me")
@jwt_required
def me():
    uid = g.current_user.get("sub")
    user = mongo.db.users.find_one({"_id": uid})
    if not user:
        return err("User not found", 404)
    student = None
    if user.get("student_ref"):
        student = mongo.db.students.find_one({"_id": user["student_ref"]})
    body = {"user": public_user(user, student)}
    if student:
        body["student"] = student_to_api(student)
    return ok(body)


@auth_bp.post("/register-lecturer")
def register_lecturer():
    data = request.get_json(force=True, silent=True) or {}
    name = str(data.get("name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    if not name or not email or not password:
        return err("name, email and password are required", 400)
    if len(password) < 6:
        return err("Password must be at least 6 characters", 400)
    if find_user_by_email(email):
        return err("Email already registered", 409)

    # simple sequential lecturer id
    count = mongo.db.users.count_documents({"role": "lecturer"})
    uid = f"usr-lec-{count + 1}"
    user_doc = {
        "_id": uid,
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": "lecturer",
        "isActive": True,
        "approvalStatus": "pending",
        "createdAt": datetime.now(timezone.utc),
    }
    mongo.db.users.insert_one(user_doc)
    return ok({"status": "pending_approval", "user": public_user(user_doc, None)}, 201)


@auth_bp.get("/lecturer-requests")
@jwt_required
def lecturer_requests():
    if g.current_user.get("role") != "admin":
        return err("Forbidden", 403)
    rows = list(
        mongo.db.users.find({"role": "lecturer", "approvalStatus": "pending"}).sort("createdAt", -1)
    )
    out = [
        {
            "id": str(r["_id"]),
            "name": r.get("name"),
            "email": r.get("email"),
            "approvalStatus": r.get("approvalStatus", "pending"),
        }
        for r in rows
    ]
    return ok({"requests": out})


@auth_bp.post("/lecturer-requests/<user_id>/approve")
@jwt_required
def approve_lecturer(user_id: str):
    if g.current_user.get("role") != "admin":
        return err("Forbidden", 403)
    res = mongo.db.users.update_one(
        {"_id": user_id, "role": "lecturer"},
        {"$set": {"approvalStatus": "approved"}},
    )
    if res.matched_count == 0:
        return err("Request not found", 404)
    return ok({"status": "approved", "userId": user_id})


@auth_bp.post("/lecturer-requests/<user_id>/reject")
@jwt_required
def reject_lecturer(user_id: str):
    if g.current_user.get("role") != "admin":
        return err("Forbidden", 403)
    res = mongo.db.users.update_one(
        {"_id": user_id, "role": "lecturer"},
        {"$set": {"approvalStatus": "rejected", "isActive": False}},
    )
    if res.matched_count == 0:
        return err("Request not found", 404)
    return ok({"status": "rejected", "userId": user_id})
