from flask import Flask

from app.routes.alerts import alerts_bp
from app.routes.analytics import analytics_bp
from app.routes.attendance import attendance_bp
from app.routes.auth import auth_bp
from app.routes.emotions import emotions_bp
from app.routes.face import face_bp
from app.routes.students import students_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(face_bp, url_prefix="/api/face")
    app.register_blueprint(emotions_bp, url_prefix="/api/emotions")
