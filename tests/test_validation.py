"""Validation contract tests unrelated to the deliberate blank-title defect."""

import pytest

from app.validators import (
    TaskValidationError,
    validate_completed,
    validate_task_payload,
    validate_title,
)


def test_title_is_trimmed_and_normalized():
    assert validate_title("  Buy milk  ") == "Buy milk"


def test_title_accepts_maximum_supported_length():
    assert validate_title("x" * 120) == "x" * 120


@pytest.mark.parametrize("bad_value", [None, False, 42, [], {}])
def test_title_rejects_non_string_values(bad_value):
    with pytest.raises(TaskValidationError, match="string"):
        validate_title(bad_value)


def test_title_rejects_overlong_values():
    with pytest.raises(TaskValidationError, match="120"):
        validate_title("x" * 121)


@pytest.mark.parametrize("value", [True, False])
def test_completion_accepts_real_booleans(value):
    assert validate_completed(value) is value


@pytest.mark.parametrize("value", [None, 0, 1, "true", "false", []])
def test_completion_rejects_non_booleans(value):
    with pytest.raises(TaskValidationError, match="boolean"):
        validate_completed(value)


def test_task_payload_normalizes_and_preserves_false():
    assert validate_task_payload(
        {"title": "  Review changes  ", "completed": False}, partial=False
    ) == {"title": "Review changes", "completed": False}


def test_partial_update_can_contain_only_title():
    assert validate_task_payload({"title": "Updated"}, partial=True) == {
        "title": "Updated"
    }
