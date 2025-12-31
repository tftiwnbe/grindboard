from fastapi.testclient import TestClient

from tests.conftest import login as _login



def test_login_creates_user_and_returns_token(client: TestClient):
    status, body = _login(client, "alice", "secret123")
    assert status == 200

    token = body.get("token")
    assert isinstance(token, str) and len(token) > 0


def test_login_requires_non_empty_username(client: TestClient):
    status, _ = _login(client, "", "secret123")
    assert status == 422


def test_login_rejects_whitespace_only_username(client: TestClient):
    status, _ = _login(client, "   \t  ", "secret123")
    assert status == 422


def test_login_trims_username(client: TestClient):
    status, body = _login(client, "  bob  ")
    assert status == 200
    assert "token" in body
    # Re-login with already-trimmed username should also succeed
    status2, body2 = _login(client, "bob")
    assert status2 == 200 and isinstance(body2.get("token"), str)


def test_login_rejects_long_username(client: TestClient):
    too_long = "x" * 151
    status, _ = _login(client, too_long)
    assert status == 422


def test_login_requires_min_password_length(client: TestClient):
    status, _ = _login(client, "charlie", "short")  # 5 chars
    assert status == 422
