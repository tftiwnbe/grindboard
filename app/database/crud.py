from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import schemas
from app.database import models


async def get_tasks(db: AsyncSession, user: models.User):
    stmt = select(models.Task).where(models.Task.user_id == user.id)
    tasks = (await db.scalars(stmt)).all()
    return tasks


async def create_task(
    db: AsyncSession, task: schemas.TaskCreate, user: models.User
):
    payload = task.model_dump(exclude_unset=True)
    payload["user_id"] = user.id
    task_db = models.Task(**payload)
    db.add(task_db)
    await db.commit()
    return task_db


async def update_task(
    db: AsyncSession,
    task: schemas.TaskUpdate,
    task_id: int,
    user: models.User,
):
    stmt = select(models.Task).where(
        models.Task.id == task_id, models.Task.user_id == user.id
    )
    task_db = (await db.scalars(stmt)).first()
    if not task_db:
        return None

    updates: dict[str, str | bool] = task.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(task_db, key, value)
    await db.commit()
    return task_db


async def complete_task(
    db: AsyncSession, task_id: int, user: models.User
):
    stmt = select(models.Task).where(
        models.Task.id == task_id, models.Task.user_id == user.id
    )
    task_db = (await db.scalars(stmt)).first()
    if not task_db:
        return None

    if not task_db.completed:
        task_db.completed = True
    else:
        task_db.completed = False

    await db.commit()
    return task_db


async def delete_task(db: AsyncSession, task_id: int, user: models.User):
    stmt = select(models.Task).where(
        models.Task.id == task_id, models.Task.user_id == user.id
    )
    task_db = (await db.scalars(stmt)).first()
    if not task_db:
        return None

    await db.delete(task_db)
    await db.commit()
    return task_db


async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    stmt = select(models.User).where(models.User.username == username)
    return (await db.scalars(stmt)).first()


async def create_user(
    db: AsyncSession, *, username: str, password_hash: str
) -> models.User:
    user = models.User(username=username, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
