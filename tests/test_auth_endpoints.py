import pytest
from httpx import AsyncClient


class TestLogin:
    """Tests for POST /auth/login endpoint."""

    async def test_creates_user_and_returns_token(self, client: AsyncClient):
        """First login should create user and return valid token."""
        response = await client.post(
            "/auth/login", json={"username": "alice", "password": "secret123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0

    async def test_subsequent_login_returns_token(self, client: AsyncClient):
        """Logging in twice with same credentials should work."""
        credentials = {"username": "bob", "password": "password123"}

        # First login
        r1 = await client.post("/auth/login", json=credentials)
        assert r1.status_code == 200
        token1 = r1.json()["token"]

        # Second login
        r2 = await client.post("/auth/login", json=credentials)
        assert r2.status_code == 200
        token2 = r2.json()["token"]

        # Both should be valid tokens
        assert isinstance(token1, str) and len(token1) > 0
        assert isinstance(token2, str) and len(token2) > 0

    async def test_username_is_trimmed(self, client: AsyncClient):
        """Whitespace around username should be trimmed."""
        # Login with whitespace
        r1 = await client.post(
            "/auth/login", json={"username": "  charlie  ", "password": "pass123"}
        )
        assert r1.status_code == 200

        # Login without whitespace should work (same user)
        r2 = await client.post(
            "/auth/login", json={"username": "charlie", "password": "pass123"}
        )
        assert r2.status_code == 200


class TestLoginValidation:
    """Tests for login input validation."""

    @pytest.mark.parametrize(
        "username,password,reason",
        [
            ("", "password123", "empty username"),
            ("   ", "password123", "whitespace-only username"),
            ("  \t\n  ", "password123", "whitespace-only username with tabs/newlines"),
            ("x" * 151, "password123", "username too long (>150 chars)"),
            ("validuser", "short", "password too short (<8 chars)"),
            ("validuser", "", "empty password"),
        ],
    )
    async def test_validation_errors(
        self, client: AsyncClient, username: str, password: str, reason: str
    ):
        """Login should reject invalid inputs."""
        response = await client.post(
            "/auth/login", json={"username": username, "password": password}
        )
        assert response.status_code == 422, f"Expected 422 for: {reason}"
