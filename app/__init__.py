"""Flask application factory for the BugHound demonstration target."""

from flask import Flask

from app.routes import tasks_blueprint
from app.services import TaskService


def create_app(config: dict | None = None) -> Flask:
    """Create an application with a fresh, in-memory task store."""
    app = Flask(__name__)
    if config is not None:
        app.config.update(config)

    app.extensions["task_service"] = TaskService()
    app.register_blueprint(tasks_blueprint)
    return app
