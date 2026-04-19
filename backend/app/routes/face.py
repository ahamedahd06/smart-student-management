from flask import Blueprint, g, request

from app.extensions import mongo
from app.ml import face_service
from app.routes.middleware import jwt_required
from app.utils.responses import err, ok

face_bp = Blueprint("face", __name__)


@face_bp.post("/enroll")
@jwt_required
def enroll():
    if g.current_user.get("role") != "student":
        return err("Only students may enroll a face template", 403)
    student_ref = g.current_user.get("student_ref")
    if not student_ref:
        return err("Student profile not linked", 400)
    if "image" not in request.files:
        return err("Image file required (field name: image)", 400)
    image_bytes = request.files["image"].read()
    if not image_bytes:
        return err("Empty image", 400)

    if not face_service.face_available():
        return err(
            "face_recognition is not installed on this server. "
            "Use SKIP_FACE_VERIFICATION=1 for demo, or install dlib/face_recognition (Linux/WSL recommended).",
            503,
        )

    enc = face_service.encode_face(image_bytes)
    if not enc:
        return err("No face detected — use a clear frontal photo", 400)

    mongo.db.students.update_one(
        {"_id": student_ref},
        {"$set": {"face_encoding": enc, "facialSignature": "enrolled"}},
    )
    return ok({"status": "enrolled", "message": "Face template saved for verification"})
