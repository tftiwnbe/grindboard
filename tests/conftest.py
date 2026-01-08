"""Test configuration with in-memory database and transaction rollback."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from alembic import command
from alembic.config import Config
from app.core.database import get_database_session
from app.main import app


# ============================================================================
# Event Loop Setup
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Setup - One migration run, transaction rollback per test
# ============================================================================


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create in-memory SQLite database and run migrations once.
    This is shared across all tests in the session.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Run migrations once for the entire test session
    async with engine.begin() as conn:
        await conn.run_sync(_run_migrations)

    yield engine

    await engine.dispose()


def _run_migrations(connection):
    """Run alembic migrations synchronously."""
    cfg = Config("alembic.ini")
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture
async def db(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session with automatic rollback.
    Each test gets a fresh transaction that is rolled back after the test.
    """
    # Create a new connection for this test
    async with engine.connect() as connection:
        # Start a transaction
        async with connection.begin() as transaction:
            # Create session bound to this transaction
            session_maker = async_sessionmaker(
                bind=connection,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            async with session_maker() as session:
                yield session

            # Transaction automatically rolls back here
            await transaction.rollback()


# ============================================================================
# HTTP Client Setup
# ============================================================================


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide async HTTP client with database dependency override.
    Uses HTTPX AsyncClient for true async support.
    """

    async def override_get_db():
        yield db

    app.dependency_overrides[get_database_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ============================================================================
# Authentication Helpers
# ============================================================================


@pytest.fixture
def make_user(client: AsyncClient):
    """Helper to create and login a user."""

    async def _make_user(username: str = "testuser", password: str = "password123"):
        response = await client.post(
            "/auth/login", json={"username": username, "password": password}
        )
        assert response.status_code == 200
        data = response.json()
        return data["token"]

    return _make_user


@pytest_asyncio.fixture
async def auth_token(make_user) -> str:
    """Provide authentication token for default test user."""
    return await make_user()


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Provide authentication headers."""
    return {"Authorization": f"Bearer {auth_token}"}


# ============================================================================
# Task Helpers
# ============================================================================


@pytest.fixture
def make_task(client: AsyncClient, auth_headers: dict[str, str]):
    """Helper to create tasks in tests."""

    async def _make_task(
        title: str = "Test Task", description: str = "Test Description", **kwargs
    ):
        payload = {"title": title, "description": description, **kwargs}
        response = await client.post("/tasks/", json=payload, headers=auth_headers)
        assert response.status_code == 200
        return response.json()

    return _make_task
