import os
from flask import Flask
from app_db import init_db
from pathlib import Path


def create_app():
    base_dir = Path(__file__).resolve().parent.parent
    templates_dir = str(base_dir / "templates")
    static_dir = str(base_dir / "static")
    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir,
        static_url_path="/static",
    )
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
    init_db()

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
