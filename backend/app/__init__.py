"""Aplicação de legendagem de vídeos em inglês."""

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    from app.routes import main_bp
    from app.document_routes import documents_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(documents_bp)
    return app
