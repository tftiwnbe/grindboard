from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import schemas
from app.config import settings
from app.database import models


async def get_tasks(db: AsyncSession, user: models.User | None = None):
    stmt = select(models.Task)
    if user is not None:
        stmt = stmt.where(models.Task.user_id == user.id)
    tasks = (await db.scalars(stmt)).all()
    return tasks


async def create_task(
    db: AsyncSession, task: schemas.TaskCreate, user: models.User | None = None
):
    payload = task.model_dump(exclude_unset=True)
    if user is not None:
        payload["user_id"] = user.id
    task_db = models.Task(**payload)
    db.add(task_db)
    await db.commit()
    return task_db


async def update_task(
    db: AsyncSession,
    task: schemas.TaskUpdate,
    task_id: int,
    user: models.User | None = None,
):
    stmt = select(models.Task).where(models.Task.id == task_id)
    if user is not None:
        stmt = stmt.where(models.Task.user_id == user.id)
    task_db = (await db.scalars(stmt)).first()
    if not task_db:
        return None

    updates: dict[str, str | bool] = task.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(task_db, key, value)
    await db.commit()
    return task_db


async def complete_task(
    db: AsyncSession, task_id: int, user: models.User | None = None
):
    stmt = select(models.Task).where(models.Task.id == task_id)
    if user is not None:
        stmt = stmt.where(models.Task.user_id == user.id)
    task_db = (await db.scalars(stmt)).first()
    if not task_db:
        return None

    if not task_db.completed:
        task_db.completed = True
    else:
        task_db.completed = False

    await db.commit()
    return task_db


async def delete_task(db: AsyncSession, task_id: int, user: models.User | None = None):
    stmt = select(models.Task).where(models.Task.id == task_id)
    if user is not None:
        stmt = stmt.where(models.Task.user_id == user.id)
    task_db = (await db.scalars(stmt)).first()
    if not task_db:
        return None

    await db.delete(task_db)
    await db.commit()
    return task_db


async def cleanup_expired_tokens(db: AsyncSession, user_id: int | None = None) -> None:
    now = datetime.now(timezone.utc)
    cond = models.AuthToken.expires_at.is_not(None) & (
        models.AuthToken.expires_at < now
    )
    if user_id is not None:
        cond = cond & (models.AuthToken.user_id == user_id)
    _deleted_token = await db.execute(delete(models.AuthToken).where(cond))


async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    stmt = select(models.User).where(models.User.username == username)
    return (await db.scalars(stmt)).first()


async def create_token(db: AsyncSession, user: models.User) -> models.AuthToken:
    await cleanup_expired_tokens(db, user_id=user.id)

    max_tokens = max(1, getattr(settings, "max_tokens_per_user", 1))
    if max_tokens == 1:
        existing = await db.scalars(
            select(models.AuthToken).where(models.AuthToken.user_id == user.id)
        )
        for t in existing:
            await db.delete(t)
    else:
        tokens = (
            await db.scalars(
                select(models.AuthToken)
                .where(models.AuthToken.user_id == user.id)
                .order_by(models.AuthToken.id.desc())
            )
        ).all()
        keep = max_tokens - 1
        for t in tokens[keep:]:
            await db.delete(t)

    ttl = timedelta(minutes=settings.token_ttl_minutes)
    expires_at = datetime.now(timezone.utc) + ttl

    import secrets as _secrets  # local import to avoid top-level coupling

    token_value = _secrets.token_urlsafe(48)
    token = models.AuthToken(token=token_value, user_id=user.id, expires_at=expires_at)
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def create_user(
    db: AsyncSession, *, username: str, password_hash: str
) -> models.User:
    user = models.User(username=username, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
