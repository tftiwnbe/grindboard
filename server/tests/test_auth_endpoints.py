import pytest
from httpx import AsyncClient


class TestRegister:
    """Tests for POST /auth/register endpoint."""

    async def test_register_new_user_returns_token(self, client: AsyncClient):
        """Registration should create user and return valid token."""
        response = await client.post(
            "/api/v1/auth/register", json={"username": "alice", "password": "secret123"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0

    async def test_register_duplicate_username_returns_409(self, client: AsyncClient):
        """Registering with an existing username should return 409."""
        credentials = {"username": "dupuser", "password": "password123"}
        r1 = await client.post("/api/v1/auth/register", json=credentials)
        assert r1.status_code == 201

        r2 = await client.post("/api/v1/auth/register", json=credentials)
        assert r2.status_code == 409


class TestLogin:
    """Tests for POST /auth/login endpoint."""

    async def test_login_returns_token(self, client: AsyncClient):
        """Login with valid credentials should return a token."""
        credentials = {"username": "loginbob", "password": "password123"}
        await client.post("/api/v1/auth/register", json=credentials)

        response = await client.post("/api/v1/auth/login", json=credentials)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert isinstance(data["token"], str)

    async def test_login_twice_returns_tokens(self, client: AsyncClient):
        """Logging in twice with same credentials should work."""
        credentials = {"username": "bob", "password": "password123"}
        await client.post("/api/v1/auth/register", json=credentials)

        r1 = await client.post("/api/v1/auth/login", json=credentials)
        assert r1.status_code == 200

        r2 = await client.post("/api/v1/auth/login", json=credentials)
        assert r2.status_code == 200

    async def test_login_unknown_user_returns_401(self, client: AsyncClient):
        """Login with unknown username should return 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "password123"},
        )
        assert response.status_code == 401

    async def test_login_wrong_password_returns_401(self, client: AsyncClient):
        """Login with wrong password should return 401."""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "wrongpass", "password": "correctpassword"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "wrongpass", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_username_is_trimmed(self, client: AsyncClient):
        """Whitespace around username should be trimmed."""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "charlie", "password": "pass123"},
        )
        r1 = await client.post(
            "/api/v1/auth/login",
            json={"username": "  charlie  ", "password": "pass123"},
        )
        assert r1.status_code == 200


class TestLoginValidation:
    """Tests for login/register input validation."""

    @pytest.mark.parametrize(
        "username,password,reason",
        [
            ("", "password123", "empty username"),
            ("   ", "password123", "whitespace-only username"),
            ("  \t\n  ", "password123", "whitespace-only username with tabs/newlines"),
            ("x" * 151, "password123", "username too long (>150 chars)"),
            ("validuser", "short", "password too short (<6 chars)"),
            ("validuser", "", "empty password"),
        ],
    )
    async def test_login_validation_errors(
        self, client: AsyncClient, username: str, password: str, reason: str
    ):
        """Login should reject invalid inputs."""
        response = await client.post(
            "/api/v1/auth/login", json={"username": username, "password": password}
        )
        assert response.status_code == 422, f"Expected 422 for: {reason}"

    @pytest.mark.parametrize(
        "username,password,reason",
        [
            ("", "password123", "empty username"),
            ("   ", "password123", "whitespace-only username"),
            ("x" * 151, "password123", "username too long (>150 chars)"),
            ("validuser", "short", "password too short (<6 chars)"),
            ("validuser", "", "empty password"),
        ],
    )
    async def test_register_validation_errors(
        self, client: AsyncClient, username: str, password: str, reason: str
    ):
        """Register should reject invalid inputs."""
        response = await client.post(
            "/api/v1/auth/register", json={"username": username, "password": password}
        )
        assert response.status_code == 422, f"Expected 422 for: {reason}"
