"""Input validation for task creation and partial updates."""


class TaskValidationError(ValueError):
    """Raised for invalid client-supplied task data."""


def validate_title(value: object) -> str:
    """Return a normalized title (at most 120 characters)."""
    if not isinstance(value, str):
        raise TaskValidationError("title must be a string")

    normalized = value.strip()
    if len(normalized) > 120:
        raise TaskValidationError("title must be at most 120 characters")
    return normalized


def validate_completed(value: object) -> bool:
    """Require an actual JSON boolean, not a truthy lookalike."""
    if not isinstance(value, bool):
        raise TaskValidationError("completed must be a boolean")
    return value


def validate_task_payload(payload: object, *, partial: bool) -> dict:
    """Validate a JSON object and return only normalized supported fields."""
    if not isinstance(payload, dict):
        raise TaskValidationError("request body must be a JSON object")

    unknown = set(payload) - {"title", "completed"}
    if unknown:
        raise TaskValidationError("unknown task fields: " + ", ".join(sorted(unknown)))

    if not partial and "title" not in payload:
        raise TaskValidationError("title is required")
    if partial and not payload:
        raise TaskValidationError("at least one field must be provided")

    normalized = {}
    if "title" in payload:
        normalized["title"] = validate_title(payload["title"])
    if "completed" in payload:
        normalized["completed"] = validate_completed(payload["completed"])
    return normalized
