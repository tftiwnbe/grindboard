from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import schemas
from app.database import models


async def get_tasks(db: AsyncSession):
    tasks = (await db.scalars(select(models.Task))).all()
    return tasks


async def create_task(db: AsyncSession, task: schemas.TaskCreate):
    task_db = models.Task(**task.model_dump(exclude_unset=True))
    db.add(task_db)
    await db.commit()
    return task_db


async def update_task(db: AsyncSession, task: schemas.TaskUpdate, task_id: int):
    task_db = (
        await db.scalars(select(models.Task).where(models.Task.id == task_id))
    ).first()
    if not task_db:
        return None

    updates: dict[str, str | bool] = task.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(task_db, key, value)
    await db.commit()
    return task_db


async def complete_task(db: AsyncSession, task_id: int):
    task_db = (
        await db.scalars(select(models.Task).where(models.Task.id == task_id))
    ).first()
    if not task_db:
        return None

    if not task_db.completed:
        task_db.completed = True
    else:
        task_db.completed = False

    await db.commit()
    return task_db


async def delete_task(db: AsyncSession, task_id: int):
    task_db = (
        await db.scalars(select(models.Task).where(models.Task.id == task_id))
    ).first()
    if not task_db:
        return None

    await db.delete(task_db)
    await db.commit()
    return task_db
