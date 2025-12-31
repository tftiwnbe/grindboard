from typing import Any, cast

from fastapi.testclient import TestClient

from app.api.schemas import Task


def _create_task(client: TestClient, headers: dict[str, str], **overrides: object) -> Task:
    payload: dict[str, Any] = {
        "title": "write tests",
        "description": "cover CRUD",
    } | overrides
    r = client.post("/tasks/", json=payload, headers=headers)
    assert r.status_code == 200
    # Parse JSON into Pydantic model for attribute access
    return Task.model_validate(r.json())


def test_list_empty(client: TestClient, auth_headers: dict[str, str]):
    r = client.get("/tasks/", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_create_returns_task(client: TestClient, auth_headers: dict[str, str]):
    data = _create_task(client, auth_headers, title="t1", description="d1")
    assert data.id is not None
    assert data.title == "t1"
    assert data.description == "d1"
    assert data.completed is False


def test_update_returns_update_fields_only(client: TestClient, auth_headers: dict[str, str]):
    created = _create_task(client, auth_headers, title="old")
    r = client.put(f"/tasks/{created.id}", json={"title": "new"}, headers=auth_headers)
    assert r.status_code == 200
    body = cast(dict[str, Any], r.json())
    assert body["title"] == "new"
    assert "completed" not in body and "id" not in body  # TaskUpdate response_model


def test_complete_toggles(client: TestClient, auth_headers: dict[str, str]):
    created = _create_task(client, auth_headers, title="toggle")
    tid = created.id
    r1 = client.post(f"/tasks/{tid}/complete", headers=auth_headers)
    assert r1.status_code == 200 and r1.json()["completed"] is True
    r2 = client.post(f"/tasks/{tid}/complete", headers=auth_headers)
    assert r2.status_code == 200 and r2.json()["completed"] is False


def test_delete_removes_from_list(client: TestClient, auth_headers: dict[str, str]):
    created = _create_task(client, auth_headers, title="to delete")
    tid = created.id
    del_r = client.delete(f"/tasks/{tid}", headers=auth_headers)
    assert del_r.status_code == 200
    lst_json = cast(list[Task], client.get("/tasks/", headers=auth_headers).json())
    lst = [Task.model_validate(item) for item in lst_json]
    assert all(item.id != tid for item in lst)


def test_validation_error_on_create(client: TestClient, auth_headers: dict[str, str]):
    r = client.post("/tasks/", json={"description": "missing title"}, headers=auth_headers)
    assert r.status_code == 422


def test_update_not_found(client: TestClient, auth_headers: dict[str, str]):
    r = client.put("/tasks/999999", json={"title": "x"}, headers=auth_headers)
    assert r.status_code == 404
    r = client.post("/tasks/999999/complete", headers=auth_headers)
    assert r.status_code == 404


def test_delete_not_found(client: TestClient, auth_headers: dict[str, str]):
    r = client.delete("/tasks/999999", headers=auth_headers)
    assert r.status_code == 404


def test_requires_auth(client: TestClient):
    r = client.get("/tasks/")
    assert r.status_code == 401
