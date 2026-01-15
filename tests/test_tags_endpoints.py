import pytest
from httpx import AsyncClient


class TestListTags:
    """Tests for GET /tags/ endpoint."""

    async def test_empty_list(self, client: AsyncClient, auth_headers: dict[str, str]):
        """New user should have empty tag list."""
        response = await client.get("/api/v1/tags/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    async def test_lists_created_tags(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should list all tags created by user."""
        # Create tags
        await client.post("/api/v1/tags/?name=work", headers=auth_headers)
        await client.post("/api/v1/tags/?name=personal", headers=auth_headers)

        response = await client.get("/api/v1/tags/", headers=auth_headers)

        assert response.status_code == 200
        tags = response.json()
        assert len(tags) == 2
        tag_names = [t["name"] for t in tags]
        assert "work" in tag_names
        assert "personal" in tag_names


class TestCreateTag:
    """Tests for POST /tags/ endpoint."""

    async def test_creates_tag(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Should create tag and return it with ID."""
        response = await client.post("/api/v1/tags/?name=urgent", headers=auth_headers)

        assert response.status_code == 200
        tag = response.json()
        assert tag["id"] is not None
        assert tag["name"] == "urgent"

    async def test_prevents_duplicate_tags(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Creating tag with same name should return existing tag."""
        # Create tag
        r1 = await client.post("/api/v1/tags/?name=work", headers=auth_headers)
        tag1 = r1.json()

        # Try to create duplicate
        r2 = await client.post("/api/v1/tags/?name=work", headers=auth_headers)
        tag2 = r2.json()

        assert r2.status_code == 200
        assert tag1["id"] == tag2["id"]

        # Verify only one tag exists
        list_response = await client.get("/api/v1/tags/", headers=auth_headers)
        assert len(list_response.json()) == 1


class TestRenameTag:
    """Tests for PUT /tags/{id} endpoint."""

    async def test_renames_tag(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Should rename tag successfully."""
        # Create tag
        create_response = await client.post(
            "/api/v1/tags/?name=old_name", headers=auth_headers
        )
        tag_id = create_response.json()["id"]

        # Rename tag
        response = await client.put(
            f"/api/v1/tags/{tag_id}?name=new_name", headers=auth_headers
        )

        assert response.status_code == 200
        tag = response.json()
        assert tag["name"] == "new_name"
        assert tag["id"] == tag_id

    async def test_merge_on_duplicate_name(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Renaming to existing tag name should merge tags."""
        # Create two tags
        r1 = await client.post("/api/v1/tags/?name=tag1", headers=auth_headers)
        tag1_id = r1.json()["id"]

        r2 = await client.post("/api/v1/tags/?name=tag2", headers=auth_headers)
        tag2_id = r2.json()["id"]

        # Create task and add tag1 to it
        task = await make_task(title="Test Task")
        await client.post(
            f"/api/v1/tags/tasks/{task['id']}/tags/{tag1_id}", headers=auth_headers
        )

        # Rename tag2 to tag1 (should merge)
        response = await client.put(
            f"/api/v1/tags/{tag2_id}?name=tag1", headers=auth_headers
        )
        assert response.status_code == 200
        merged_tag = response.json()
        assert merged_tag["name"] == "tag1"
        assert merged_tag["id"] == tag1_id  # Should return existing tag

        # Verify only one tag exists now
        list_response = await client.get("/api/v1/tags/", headers=auth_headers)
        tags = list_response.json()
        assert len(tags) == 1
        assert tags[0]["name"] == "tag1"

    async def test_rename_nonexistent_tag(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should return 404 for nonexistent tag."""
        response = await client.put(
            "/api/v1/tags/999999?name=new_name", headers=auth_headers
        )
        assert response.status_code == 404


class TestDeleteTag:
    """Tests for DELETE /tags/{id} endpoint."""

    async def test_deletes_tag(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Should delete tag."""
        # Create tag
        create_response = await client.post(
            "/api/v1/tags/?name=to_delete", headers=auth_headers
        )
        tag_id = create_response.json()["id"]

        # Delete tag
        response = await client.delete(f"/api/v1/tags/{tag_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify it's gone
        list_response = await client.get("/api/v1/tags/", headers=auth_headers)
        tags = list_response.json()
        assert not any(t["id"] == tag_id for t in tags)

    async def test_delete_removes_from_tasks(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Deleting tag should remove it from all tasks."""
        # Create tag and task
        tag_response = await client.post(
            "/api/v1/tags/?name=test_tag", headers=auth_headers
        )
        tag_id = tag_response.json()["id"]

        task = await make_task(title="Test Task")

        # Add tag to task
        await client.post(
            f"/api/v1/tags/tasks/{task['id']}/tags/{tag_id}", headers=auth_headers
        )

        # Delete tag
        await client.delete(f"/api/v1/tags/{tag_id}", headers=auth_headers)

        # Task should still exist but without the tag
        task_response = await client.get("/api/v1/tasks/", headers=auth_headers)
        tasks = task_response.json()
        assert len(tasks) == 1

    async def test_delete_nonexistent_tag(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should return 404 for nonexistent tag."""
        response = await client.delete("/api/v1/tags/999999", headers=auth_headers)
        assert response.status_code == 404


class TestAddTagToTask:
    """Tests for POST /api/v1/tags/tasks/{task_id}/tags/{tag_id} endpoint."""

    async def test_adds_existing_tag_to_task(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should add existing tag to task."""
        # Create tag and task
        tag_response = await client.post(
            "/api/v1/tags/?name=important", headers=auth_headers
        )
        tag_id = tag_response.json()["id"]

        task = await make_task(title="Test Task")

        # Add tag to task
        response = await client.post(
            f"/api/v1/tags/tasks/{task['id']}/tags/{tag_id}", headers=auth_headers
        )

        assert response.status_code == 200
        tag = response.json()
        assert tag["id"] == tag_id

    async def test_idempotent_add(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Adding same tag twice should be idempotent."""
        tag_response = await client.post(
            "/api/v1/tags/?name=test", headers=auth_headers
        )
        tag_id = tag_response.json()["id"]

        task = await make_task(title="Test Task")

        # Add tag twice
        r1 = await client.post(
            f"/api/v1/tags/tasks/{task['id']}/tags/{tag_id}", headers=auth_headers
        )
        r2 = await client.post(
            f"/api/v1/tags/tasks/{task['id']}/tags/{tag_id}", headers=auth_headers
        )

        assert r1.status_code == 200
        assert r2.status_code == 200

    async def test_add_tag_to_nonexistent_task(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should return 404 for nonexistent task."""
        tag_response = await client.post(
            "/api/v1/tags/?name=test", headers=auth_headers
        )
        tag_id = tag_response.json()["id"]

        response = await client.post(
            f"/api/v1/tags/tasks/999999/tags/{tag_id}", headers=auth_headers
        )
        assert response.status_code == 404

    async def test_add_nonexistent_tag_to_task(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should return 404 for nonexistent tag."""
        task = await make_task(title="Test Task")

        response = await client.post(
            f"/api/v1/tags/tasks/{task['id']}/tags/999999", headers=auth_headers
        )
        assert response.status_code == 404


class TestRemoveTagFromTask:
    """Tests for DELETE /api/v1/tags/tasks/{task_id}/tags/{tag_id} endpoint."""

    async def test_removes_tag_from_task(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should remove tag from task."""
        # Create tag and task, then link them
        tag_response = await client.post(
            "/api/v1/tags/?name=test", headers=auth_headers
        )
        tag_id = tag_response.json()["id"]

        task = await make_task(title="Test Task")

        await client.post(
            f"/api/v1/tags/tasks/{task['id']}/tags/{tag_id}", headers=auth_headers
        )

        # Remove tag
        response = await client.delete(
            f"/api/v1/tags/tasks/{task['id']}/tags/{tag_id}", headers=auth_headers
        )

        assert response.status_code == 200

    async def test_remove_nonexistent_link(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Removing non-linked tag should succeed."""
        tag_response = await client.post(
            "/api/v1/tags/?name=test", headers=auth_headers
        )
        tag_id = tag_response.json()["id"]

        task = await make_task(title="Test Task")

        response = await client.delete(
            f"/api/v1/tags/tasks/{task['id']}/tags/{tag_id}", headers=auth_headers
        )

        assert response.status_code == 200


class TestCreateAndAddTag:
    """Tests for POST /api/v1/tags/tasks/{task_id}/tags endpoint."""

    async def test_creates_and_adds_new_tag(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should create new tag and add it to task."""
        task = await make_task(title="Test Task")

        response = await client.post(
            f"/api/v1/tags/tasks/{task['id']}/tags?name=new_tag", headers=auth_headers
        )

        assert response.status_code == 200
        tag = response.json()
        assert tag["name"] == "new_tag"
        assert tag["id"] is not None

        # Verify tag was created
        list_response = await client.get("/api/v1/tags/", headers=auth_headers)
        tags = list_response.json()
        assert any(t["name"] == "new_tag" for t in tags)

    async def test_uses_existing_tag(
        self, client: AsyncClient, auth_headers: dict[str, str], make_task
    ):
        """Should use existing tag if name already exists."""
        # Create tag first
        tag_response = await client.post(
            "/api/v1/tags/?name=existing", headers=auth_headers
        )
        existing_tag_id = tag_response.json()["id"]

        task = await make_task(title="Test Task")

        # Create and add with same name
        response = await client.post(
            f"/api/v1/tags/tasks/{task['id']}/tags?name=existing", headers=auth_headers
        )

        assert response.status_code == 200
        tag = response.json()
        assert tag["id"] == existing_tag_id

        # Verify only one tag exists
        list_response = await client.get("/api/v1/tags/", headers=auth_headers)
        tags = list_response.json()
        assert len(tags) == 1

    async def test_create_and_add_to_nonexistent_task(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Should return 404 for nonexistent task."""
        response = await client.post(
            "/api/v1/tags/tasks/999999/tags?name=test", headers=auth_headers
        )
        assert response.status_code == 404


class TestAuthentication:
    """Tests for authentication requirements."""

    @pytest.mark.parametrize(
        "method,endpoint",
        [
            ("get", "/api/v1/tags/"),
            ("post", "/api/v1/tags/?name=test"),
            ("put", "/api/v1/tags/1?name=test"),
            ("delete", "/api/v1/tags/1"),
            ("post", "/api/v1/tags/tasks/1/tags/1"),
            ("delete", "/api/v1/tags/tasks/1/tags/1"),
            ("post", "/api/v1/tags/tasks/1/tags?name=test"),
        ],
    )
    async def test_requires_authentication(
        self, client: AsyncClient, method: str, endpoint: str
    ):
        """All tag endpoints should require authentication."""
        response = await getattr(client, method)(endpoint)
        assert response.status_code == 401
