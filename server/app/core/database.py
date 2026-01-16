import contextlib
from collections.abc import AsyncIterator, Mapping
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel.ext.asyncio.session import AsyncSession

from alembic import command, config
from app.config import get_settings


class DatabaseSessionManager:
    """Manages async SQLAlchemy engine and sessions with proper lifecycle control."""

    def __init__(self, url: str, engine_kwargs: Mapping[str, Any] | None = None):
        """Initialize the database session manager."""
        self._engine = create_async_engine(url, **(engine_kwargs or {}))
        self._sessionmaker = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
        self._closed = False

    def _ensure_open(self) -> None:
        """Raise RuntimeError if the manager has been closed."""
        if self._closed:
            raise RuntimeError("DatabaseSessionManager has been closed")

    @property
    def engine(self) -> AsyncEngine:
        """Return the async engine instance."""
        self._ensure_open()
        return self._engine

    async def close(self) -> None:
        """Close the engine and mark this manager as closed."""
        if self._closed:
            return
        await self._engine.dispose()
        self._closed = True

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """
        Provide a transactional database connection.

        The connection is automatically committed on success or rolled back on error.
        """
        self._ensure_open()
        async with self._engine.begin() as connection:
            yield connection

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Provide a database session.

        The session is automatically closed after use and rolled back on error.
        """
        self._ensure_open()
        async with self._sessionmaker() as session:
            yield session


sessionmanager = DatabaseSessionManager(get_settings().app.database_url)


async def get_database_session():
    """FastAPI dependency that yields a managed AsyncSession."""
    async with sessionmanager.session() as session:
        yield session


def _run_upgrade(connection, cfg):
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


async def run_async_upgrade() -> None:
    cfg = config.Config("alembic.ini")

    async with sessionmanager.connect() as connection:
        await connection.run_sync(_run_upgrade, cfg)
