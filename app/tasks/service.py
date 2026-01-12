from sqlmodel import asc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Task, TaskCreate, TaskUpdate, User


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, user: User) -> list[Task]:
        stmt = select(Task).where(Task.user_id == user.id).order_by(asc(Task.position))
        tasks = await self.session.scalars(stmt)
        return list(tasks.all())

    async def create(self, user: User, task_data: TaskCreate) -> Task:
        payload = task_data.model_dump(exclude_unset=True)
        payload["user_id"] = user.id

        # Assign position: put new task at the end
        stmt = select(func.max(Task.position)).where(Task.user_id == user.id)
        max_position = await self.session.scalar(stmt)
        payload["position"] = (max_position or 0.0) + 1.0

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

    async def move_task(
        self,
        task_id: int,
        user: User,
        after_id: int | None = None,
    ) -> Task | None:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
        task = (await self.session.scalars(stmt)).first()
        if not task:
            return None

        stmt = select(Task).where(Task.user_id == user.id).order_by(asc(Task.position))
        tasks = (await self.session.scalars(stmt)).all()

        if after_id is None:
            # Move to top
            first_task = tasks[0] if tasks else None
            task.position = first_task.position - 1.0 if first_task else 0.0
        else:
            after_task = next((t for t in tasks if t.id == after_id), None)
            if not after_task:
                return None

            after_index = tasks.index(after_task)
            next_task = tasks[after_index + 1] if after_index + 1 < len(tasks) else None

            task.position = (
                (after_task.position + next_task.position) / 2
                if next_task
                else after_task.position + 1.0
            )

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task
