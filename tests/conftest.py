import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import pytest
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from alembic import command
from app.core.database import get_database_session
from app.main import app as actual_app


@pytest.fixture(autouse=True)
def app() -> Generator[FastAPI, None, None]:
    yield actual_app


@pytest.fixture
def client(app: FastAPI):
    with TestClient(app) as c:
        yield c


def login(
    client: TestClient, username: str = "alice", password: str = "secret123"
) -> tuple[int, dict[str, Any]]:
    r = client.post("/auth/login", json={"username": username, "password": password})
    content_type = r.headers.get("content-type") or ""
    body = r.json() if content_type.startswith("application/json") else {}
    return r.status_code, body


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    status, body = login(client)
    assert status == 200
    token = body.get("token") or ""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def run_migrations(connection: Connection):
    config = Config("alembic.ini")
    config.set_main_option("script_location", "alembic")
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


@pytest.fixture(scope="function")
async def test_engine(
    tmp_path_factory: pytest.TempPathFactory,
) -> AsyncGenerator[AsyncEngine, None]:
    db_dir: Path = tmp_path_factory.mktemp("dbs")
    db_path = db_dir / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(run_migrations)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=test_engine, expire_on_commit=False, class_=AsyncSession
    )
    session: AsyncSession = session_factory()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="function", autouse=True)
async def session_override(
    app: FastAPI, db_session: AsyncSession
) -> AsyncGenerator[None, None]:
    async def get_db_session_override():
        yield db_session

    app.dependency_overrides[get_database_session] = get_db_session_override
    yield
    app.dependency_overrides.clear()
