import pytest
from httpx import AsyncClient


class TestListTasks:
    """Tests for GET /api/v1/tasks/ endpoint."""

    async def test_empty_list(self, client: AsyncClient, auth_headers: dict[str, str]):
        """New user should have empty task list."""
        response = await client.get("/api/v1/tasks/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    async def test_lists_created_tasks(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should list all tasks created by user."""
        # Create multiple tasks
        task1 = await make_task(title="Task 1")
        task2 = await make_task(title="Task 2")

        response = await client.get("/api/v1/tasks/", headers=auth_headers)

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert any(t["id"] == task1["id"] for t in tasks)
        assert any(t["id"] == task2["id"] for t in tasks)


class TestCreateTask:
    """Tests for POST /api/v1/tasks/ endpoint."""

    async def test_creates_task_with_all_fields(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should create task and return it with ID."""
        response = await client.post(
            "/api/v1/tasks/",
            json={"title": "Write tests", "description": "Cover all endpoints"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        task = response.json()
        assert task["id"] is not None
        assert task["title"] == "Write tests"
        assert task["description"] == "Cover all endpoints"
        assert task["completed"] is False

    async def test_validates_required_fields(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should reject task without title."""
        response = await client.post(
            "/api/v1/tasks/",
            json={"description": "No title provided"},
            headers=auth_headers,
        )

        assert response.status_code == 422


class TestUpdateTask:
    """Tests for PUT /api/v1/tasks/{id} endpoint."""

    async def test_updates_task_fields(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should update task and return only changed fields."""
        task = await make_task(title="Old Title", description="Old Description")

        response = await client.put(
            f"/api/v1/tasks/{task['id']}",
            json={"title": "New Title"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        # Should only return updated fields
        assert "id" not in data
        assert "completed" not in data

    async def test_update_nonexistent_task(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should return 404 for nonexistent task."""
        response = await client.put(
            "/api/v1/tasks/999999", json={"title": "New Title"}, headers=auth_headers
        )

        assert response.status_code == 404


class TestCompleteTask:
    """Tests for POST /tasks/{id}/complete endpoint."""

    async def test_toggles_completion_status(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should toggle task completion status."""
        task = await make_task(title="Toggle Task")
        task_id = task["id"]

        # Mark as completed
        r1 = await client.post(
            f"/api/v1/tasks/{task_id}/complete", headers=auth_headers
        )
        assert r1.status_code == 200
        assert r1.json()["completed"] is True

        # Toggle back to incomplete
        r2 = await client.post(
            f"/api/v1/tasks/{task_id}/complete", headers=auth_headers
        )
        assert r2.status_code == 200
        assert r2.json()["completed"] is False

    async def test_complete_nonexistent_task(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should return 404 for nonexistent task."""
        response = await client.post(
            "/api/v1/tasks/999999/complete", headers=auth_headers
        )
        assert response.status_code == 404


class TestDeleteTask:
    """Tests for DELETE /tasks/{id} endpoint."""

    async def test_deletes_task(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should delete task and remove from list."""
        task = await make_task(title="Delete Me")
        task_id = task["id"]

        # Delete task
        response = await client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify it's not in the list
        list_response = await client.get("/api/v1/tasks/", headers=auth_headers)
        tasks = list_response.json()
        assert not any(t["id"] == task_id for t in tasks)

    async def test_delete_nonexistent_task(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should return 404 for nonexistent task."""
        response = await client.delete("/api/v1/tasks/999999", headers=auth_headers)
        assert response.status_code == 404


class TestMoveTask:
    """Tests for POST /api/v1/tasks/{task_id}/move endpoint."""

    async def test_move_task_to_top(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Move a task to the top of the list."""
        # Create 3 tasks
        t1 = await make_task(title="Task 1")
        t2 = await make_task(title="Task 2")
        t3 = await make_task(title="Task 3")

        # Move Task 3 to top (after_id=None)
        response = await client.post(
            f"/api/v1/tasks/{t3['id']}/move", headers=auth_headers
        )
        assert response.status_code == 200
        moved_task = response.json()
        assert moved_task["id"] == t3["id"]

        # Verify order: Task 3 should be first
        list_response = await client.get("/api/v1/tasks/", headers=auth_headers)
        tasks = list_response.json()
        assert tasks[0]["id"] == t3["id"]
        # Remaining tasks follow in original order
        remaining_ids = [t["id"] for t in tasks[1:]]
        assert remaining_ids == [t1["id"], t2["id"]]

    async def test_move_task_after_another(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Move a task after another task."""
        t1 = await make_task(title="Task 1")
        t2 = await make_task(title="Task 2")
        t3 = await make_task(title="Task 3")

        # Move Task 3 after Task 1
        response = await client.post(
            f"/api/v1/tasks/{t3['id']}/move?after_id={t1['id']}", headers=auth_headers
        )
        assert response.status_code == 200
        moved_task = response.json()
        assert moved_task["id"] == t3["id"]

        # Verify order: Task 1, Task 3, Task 2
        list_response = await client.get("/api/v1/tasks/", headers=auth_headers)
        tasks = list_response.json()
        expected_order = [t1["id"], t3["id"], t2["id"]]
        assert [t["id"] for t in tasks] == expected_order

    async def test_move_nonexistent_task(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should return 404 if task does not exist."""
        response = await client.post("/api/v1/tasks/999999/move", headers=auth_headers)
        assert response.status_code == 404

    async def test_move_after_nonexistent_task(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should return 404 if after_id does not exist."""
        t1 = await make_task(title="Task 1")
        response = await client.post(
            f"/api/v1/tasks/{t1['id']}/move?after_id=999999", headers=auth_headers
        )
        assert response.status_code == 404


class TestAuthentication:
    """Tests for authentication requirements."""

    @pytest.mark.parametrize(
        "method,endpoint",
        [
            ("get", "/api/v1/tasks/"),
            ("post", "/api/v1/tasks/"),
            ("put", "/api/v1/tasks/1"),
            ("post", "/api/v1/tasks/1/complete"),
            ("delete", "/api/v1/tasks/1"),
        ],
    )
    async def test_requires_authentication(
        self, client: AsyncClient, method: str, endpoint: str
    ):
        """All task endpoints should require authentication."""
        kwargs = {}
        if method in ("post", "put"):
            kwargs["json"] = {"title": "Test"}

        response = await getattr(client, method)(endpoint, **kwargs)
        assert response.status_code == 401
