import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from flask import current_app

from app.extensions import mongo


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_token(user_doc: dict) -> str:
    payload = {
        "sub": str(user_doc["_id"]),
        "role": user_doc["role"],
        "student_ref": user_doc.get("student_ref"),
        "email": user_doc.get("email"),
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=int(current_app.config["JWT_EXP_HOURS"])),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def find_user_by_email(email: str) -> dict | None:
    return mongo.db.users.find_one({"email": email.lower().strip()})


def public_user(user_doc: dict, student_doc: dict | None) -> dict:
    out = {
        "id": str(user_doc["_id"]),
        "name": user_doc.get("name"),
        "email": user_doc.get("email"),
        "role": user_doc.get("role"),
    }
    if student_doc:
        out["studentRef"] = str(student_doc["_id"])
        out["studentId"] = student_doc.get("studentId")
    elif user_doc.get("student_ref"):
        out["studentRef"] = str(user_doc["student_ref"])
        s = mongo.db.students.find_one({"_id": user_doc["student_ref"]})
        if s:
            out["studentId"] = s.get("studentId")
    return out
