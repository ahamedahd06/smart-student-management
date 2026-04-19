from app.extensions import mongo


def get_student(student_id: str) -> dict | None:
    return mongo.db.students.find_one({"_id": student_id})


def list_students(include_inactive: bool = False) -> list[dict]:
    q = {} if include_inactive else {"isActive": {"$ne": False}}
    return list(mongo.db.students.find(q).sort("studentId", 1))


def student_to_api(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "email": doc.get("email"),
        "studentId": doc.get("studentId"),
        "department": doc.get("department"),
        "year": doc.get("year"),
        "enrollmentDate": doc.get("enrollmentDate"),
        "gpa": float(doc.get("gpa", 0)),
        "attendanceRate": int(doc.get("attendanceRate", 0)),
        "riskLevel": doc.get("riskLevel", "low"),
        "profileImage": doc.get("profileImage"),
        "facialSignature": doc.get("facialSignature"),
        "isActive": bool(doc.get("isActive", True)),
    }


def update_student_metrics(student_id: str, attendance_rate: int, risk_level: str) -> None:
    mongo.db.students.update_one(
        {"_id": student_id},
        {"$set": {"attendanceRate": attendance_rate, "riskLevel": risk_level}},
    )
