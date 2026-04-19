import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-flask-secret")
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "smart_student_db")

    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
    JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", "24"))

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    EMOTION_MODEL_PATH = os.getenv("EMOTION_MODEL_PATH", "")
    EMOTION_LABEL_MAP_PATH = os.getenv("EMOTION_LABEL_MAP_PATH", "")

    SKIP_FACE_VERIFICATION = os.getenv("SKIP_FACE_VERIFICATION", "0") == "1"