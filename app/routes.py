"""HTTP routes for the task-management API."""

from flask import Blueprint, current_app, jsonify, request

from app.validators import TaskValidationError


tasks_blueprint = Blueprint("tasks", __name__)


def _service():
    return current_app.extensions["task_service"]


def _json_body():
    if not request.is_json:
        raise TaskValidationError("Content-Type must be application/json")
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise TaskValidationError("request body must be a JSON object")
    return body


@tasks_blueprint.errorhandler(TaskValidationError)
def bad_request(exc: TaskValidationError):
    return jsonify({"error": str(exc)}), 400


@tasks_blueprint.post("/tasks")
def create_task():
    task = _service().create_task(_json_body())
    return jsonify(task), 201


@tasks_blueprint.get("/tasks")
def list_tasks():
    tasks = _service().list_tasks()
    return jsonify({"tasks": tasks, "count": len(tasks)})


@tasks_blueprint.get("/tasks/<int:task_id>")
def get_task(task_id: int):
    task = _service().get_task(task_id)
    if task is None:
        return jsonify({"error": "task not found"}), 404
    return jsonify(task)


@tasks_blueprint.patch("/tasks/<int:task_id>")
def update_task(task_id: int):
    task = _service().update_task(task_id, _json_body())
    if task is None:
        return jsonify({"error": "task not found"}), 404
    return jsonify(task)


@tasks_blueprint.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    if not _service().delete_task(task_id):
        return jsonify({"error": "task not found"}), 404
    return "", 204
