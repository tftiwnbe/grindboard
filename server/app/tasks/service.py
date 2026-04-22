from sqlalchemy.orm import selectinload
from sqlmodel import asc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import TagRead, Task, TaskCreate, TaskRead, TaskUpdate, User

REBALANCE_THRESHOLD = 1e-9


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, user: User) -> list[TaskRead]:
        stmt = (
            select(Task)
            .where(Task.user_id == user.id)
            .order_by(asc(Task.position))
            .options(selectinload(Task.tags))
        )
        tasks = await self.session.scalars(stmt)
        return [self._to_read(task) for task in tasks.all()]

    async def create(self, user: User, task_data: TaskCreate) -> TaskRead:
        payload = task_data.model_dump(exclude_unset=True)
        payload["user_id"] = user.id

        stmt = select(func.max(Task.position)).where(Task.user_id == user.id)
        max_position = await self.session.scalar(stmt)
        payload["position"] = (max_position or 0.0) + 1.0

        task = Task(**payload)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task, attribute_names=["tags"])
        return self._to_read(task)

    async def update(
        self, task_id: int, user: User, task_data: TaskUpdate
    ) -> TaskRead | None:
        stmt = (
            select(Task)
            .where(Task.id == task_id, Task.user_id == user.id)
            .options(selectinload(Task.tags))
        )
        task = (await self.session.scalars(stmt)).first()
        if not task:
            return None
        updates = task_data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(task, key, value)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task, attribute_names=["tags"])
        return self._to_read(task)

    async def toggle_complete(self, task_id: int, user: User) -> TaskRead | None:
        stmt = (
            select(Task)
            .where(Task.id == task_id, Task.user_id == user.id)
            .options(selectinload(Task.tags))
        )
        task = (await self.session.scalars(stmt)).first()
        if not task:
            return None
        task.completed = not task.completed
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task, attribute_names=["tags"])
        return self._to_read(task)

    async def delete(self, task_id: int, user: User) -> bool:
        stmt = (
            select(Task)
            .where(Task.id == task_id, Task.user_id == user.id)
        )
        task = (await self.session.scalars(stmt)).first()
        if not task:
            return False
        await self.session.delete(task)
        await self.session.commit()
        return True

    async def move_task(
        self,
        task_id: int,
        user: User,
        after_id: int | None = None,
    ) -> TaskRead | None:
        stmt = (
            select(Task)
            .where(Task.id == task_id, Task.user_id == user.id)
            .options(selectinload(Task.tags))
        )
        task = (await self.session.scalars(stmt)).first()
        if not task:
            return None

        stmt = (
            select(Task)
            .where(Task.user_id == user.id, Task.id != task_id)
            .order_by(asc(Task.position))
        )
        other_tasks = (await self.session.scalars(stmt)).all()

        if after_id is None:
            first_task = other_tasks[0] if other_tasks else None
            task.position = first_task.position - 1.0 if first_task else 0.0
        else:
            if after_id == task_id:
                await self.session.refresh(task, attribute_names=["tags"])
                return self._to_read(task)

            after_task = next((t for t in other_tasks if t.id == after_id), None)
            if not after_task:
                return None

            after_index = other_tasks.index(after_task)
            next_task = other_tasks[after_index + 1] if after_index + 1 < len(other_tasks) else None

            task.position = (
                (after_task.position + next_task.position) / 2
                if next_task
                else after_task.position + 1.0
            )

        self.session.add(task)

        all_tasks = sorted(
            list(other_tasks) + [task], key=lambda t: t.position
        )
        needs_rebalance = any(
            abs(all_tasks[i + 1].position - all_tasks[i].position) < REBALANCE_THRESHOLD
            for i in range(len(all_tasks) - 1)
        )
        if needs_rebalance:
            for i, t in enumerate(all_tasks, start=1):
                t.position = float(i)
                self.session.add(t)

        await self.session.commit()
        await self.session.refresh(task, attribute_names=["tags"])
        return self._to_read(task)

    def _to_read(self, task: Task) -> TaskRead:
        return TaskRead(
            id=task.id,
            title=task.title,
            description=task.description,
            position=task.position,
            completed=task.completed,
            tags=[
                TagRead(id=tag.id, name=tag.name)
                for tag in task.tags
                if tag.id is not None
            ],
        )
