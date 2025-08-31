from fastapi.testclient import TestClient
from typing import Any, cast

from app.api.schemas import Task
from app.main import app

client = TestClient(app)


def _create_task(client: TestClient, **overrides: object) -> Task:
    payload: dict[str, Any] = {
        "title": "write tests",
        "description": "cover CRUD",
    } | overrides
    r = client.post("/tasks/", json=payload)
    assert r.status_code == 200
    # Parse JSON into Pydantic model for attribute access
    return Task.model_validate(r.json())


def test_list_empty(client: TestClient):
    r = client.get("/tasks/")
    assert r.status_code == 200
    assert r.json() == []


def test_create_returns_task(client: TestClient):
    data = _create_task(client, title="t1", description="d1")
    assert data.id is not None
    assert data.title == "t1"
    assert data.description == "d1"
    assert data.completed is False


def test_update_returns_update_fields_only(client: TestClient):
    created = _create_task(client, title="old")
    r = client.put(f"/tasks/{created.id}", json={"title": "new"})
    assert r.status_code == 200
    body = cast(dict[str, Any], r.json())
    assert body["title"] == "new"
    assert "completed" not in body and "id" not in body  # TaskUpdate response_model


def test_complete_toggles(client: TestClient):
    created = _create_task(client, title="toggle")
    tid = created.id
    r1 = client.post(f"/tasks/{tid}/complete")
    assert r1.status_code == 200 and r1.json()["completed"] is True
    r2 = client.post(f"/tasks/{tid}/complete")
    assert r2.status_code == 200 and r2.json()["completed"] is False


def test_delete_removes_from_list(client: TestClient):
    created = _create_task(client, title="to delete")
    tid = created.id
    del_r = client.delete(f"/tasks/{tid}")
    assert del_r.status_code == 200
    lst_json = cast(list[Task], client.get("/tasks/").json())
    lst = [Task.model_validate(item) for item in lst_json]
    assert all(item.id != tid for item in lst)


def test_validation_error_on_create(client: TestClient):
    r = client.post("/tasks/", json={"description": "missing title"})
    assert r.status_code == 422


def test_update_not_found(client: TestClient):
    r = client.put("/tasks/999999", json={"title": "x"})
    assert r.status_code == 404
    r = client.post("/tasks/999999/complete")
    assert r.status_code == 404


def test_delete_not_found(client: TestClient):
    r = client.delete("/tasks/999999")
    assert r.status_code == 404
