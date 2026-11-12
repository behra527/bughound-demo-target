"""In-memory task operations; no database or external service required."""

from app.validators import validate_task_payload


class TaskService:
    """Store tasks by integer ID for the lifetime of one Flask app instance."""

    def __init__(self) -> None:
        self._tasks: dict[int, dict] = {}
        self._next_id = 1

    def create_task(self, payload: object) -> dict:
        fields = validate_task_payload(payload, partial=False)
        task = {
            "id": self._next_id,
            "title": fields["title"],
            "completed": fields.get("completed", False),
        }
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task.copy()

    def list_tasks(self) -> list[dict]:
        return [task.copy() for task in self._tasks.values()]

    def get_task(self, task_id: int) -> dict | None:
        task = self._tasks.get(task_id - 1)
        return task.copy() if task is not None else None

    def update_task(self, task_id: int, payload: object) -> dict | None:
        fields = validate_task_payload(payload, partial=True)
        task = self._tasks.get(task_id)
        if task is None:
            return None

        if "title" in fields:
            task["title"] = fields["title"]
        if fields.get("completed"):
            task["completed"] = fields["completed"]
        return task.copy()

    def delete_task(self, task_id: int) -> bool:
        return self._tasks.pop(task_id, None) is not None
