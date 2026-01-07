from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Task, TaskCreate, TaskUpdate, User


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, user: User):
        stmt = select(Task).where(Task.user_id == user.id)
        tasks = await self.session.scalars(stmt)
        return tasks.all()

    async def create(self, user: User, task_data: TaskCreate) -> Task:
        payload = task_data.model_dump(exclude_unset=True)
        payload["user_id"] = user.id
        task = Task(**payload)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update(
        self, task_id: int, user: User, task_data: TaskUpdate
    ) -> Task | None:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
        task = (await self.session.scalars(stmt)).first()
        if not task:
            return None
        updates = task_data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(task, key, value)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def toggle_complete(self, task_id: int, user: User) -> Task | None:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
        task = (await self.session.scalars(stmt)).first()
        if not task:
            return None
        task.completed = not task.completed
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, task_id: int, user: User) -> Task | None:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
        task = (await self.session.scalars(stmt)).first()
        if not task:
            return None
        await self.session.delete(task)
        await self.session.commit()
        return task
