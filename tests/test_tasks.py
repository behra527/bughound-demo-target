"""API behavior tests. Three tests expose intentional application defects."""

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    return app.test_client()


def _create(client, title="Write documentation", **extra):
    return client.post("/tasks", json={"title": title, **extra})


def test_create_task_success(client):
    response = _create(client)
    assert response.status_code == 201
    assert response.get_json() == {
        "id": 1,
        "title": "Write documentation",
        "completed": False,
    }


def test_create_task_with_explicit_completion(client):
    response = _create(client, "Already done", completed=True)
    assert response.status_code == 201
    assert response.get_json()["completed"] is True


def test_list_tasks_in_creation_order(client):
    _create(client, "First")
    _create(client, "Second")
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.get_json() == {
        "count": 2,
        "tasks": [
            {"id": 1, "title": "First", "completed": False},
            {"id": 2, "title": "Second", "completed": False},
        ],
    }


def test_empty_and_whitespace_titles_are_rejected(client):
    empty = _create(client, "")
    whitespace = _create(client, "   \t  ")
    assert [empty.status_code, whitespace.status_code] == [400, 400]


def test_get_task_returns_exact_matching_id(client):
    _create(client, "First")
    second = _create(client, "Second").get_json()
    response = client.get(f"/tasks/{second['id']}")
    assert response.status_code == 200
    assert response.get_json() == second


def test_get_missing_task_returns_404(client):
    _create(client, "Existing")
    response = client.get("/tasks/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "task not found"}


def test_update_task_title(client):
    task_id = _create(client, "Old title").get_json()["id"]
    response = client.patch(f"/tasks/{task_id}", json={"title": "New title"})
    assert response.status_code == 200
    assert response.get_json() == {
        "id": task_id,
        "title": "New title",
        "completed": False,
    }
    assert client.get("/tasks").get_json()["tasks"][0]["title"] == "New title"


def test_update_completion_to_true(client):
    task_id = _create(client, "To complete").get_json()["id"]
    response = client.patch(f"/tasks/{task_id}", json={"completed": True})
    assert response.status_code == 200
    assert response.get_json()["completed"] is True
    assert client.get("/tasks").get_json()["tasks"][0]["completed"] is True


def test_update_completion_to_false_persists(client):
    task_id = _create(client, "Reopen task", completed=True).get_json()["id"]
    response = client.patch(f"/tasks/{task_id}", json={"completed": False})
    assert response.status_code == 200
    assert response.get_json()["completed"] is False
    assert client.get("/tasks").get_json()["tasks"][0]["completed"] is False


def test_delete_task(client):
    task_id = _create(client, "Delete me").get_json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204
    assert response.data == b""
    assert client.get("/tasks").get_json() == {"tasks": [], "count": 0}
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_delete_missing_task_returns_404(client):
    response = client.delete("/tasks/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "task not found"}


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"title": 123},
        {"title": None},
        {"title": "x" * 121},
        {"title": "A task", "completed": "yes"},
        {"title": "A task", "completed": 1},
        {"title": "A task", "unexpected": True},
        ["not", "an", "object"],
    ],
)
def test_invalid_create_payload_returns_400(client, body):
    response = client.post("/tasks", json=body)
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert client.get("/tasks").get_json()["count"] == 0


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"title": 7},
        {"title": "x" * 121},
        {"completed": "false"},
        {"completed": 0},
        {"unrecognized": 1},
        ["not", "an", "object"],
    ],
)
def test_invalid_update_payload_returns_400(client, body):
    task_id = _create(client).get_json()["id"]
    response = client.patch(f"/tasks/{task_id}", json=body)
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert client.get("/tasks").get_json()["tasks"][0]["title"] == "Write documentation"


def test_missing_or_malformed_json_returns_400(client):
    no_json = client.post("/tasks", data="hello", content_type="text/plain")
    malformed = client.post("/tasks", data="{", content_type="application/json")
    assert no_json.status_code == 400
    assert malformed.status_code == 400


def test_update_unknown_task_returns_404(client):
    response = client.patch("/tasks/999", json={"title": "Does not exist"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "task not found"}


def test_separate_app_instances_have_independent_stores():
    first_client = create_app({"TESTING": True}).test_client()
    second_client = create_app({"TESTING": True}).test_client()
    _create(first_client, "Only in first app")
    assert second_client.get("/tasks").get_json() == {"tasks": [], "count": 0}
