from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import init_mongo, mongo
from app.routes import register_blueprints


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    origins = [o.strip() for o in app.config.get("CORS_ORIGINS", "").split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True)

    init_mongo(app)
    register_blueprints(app)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "db": mongo.db is not None}

    return app
