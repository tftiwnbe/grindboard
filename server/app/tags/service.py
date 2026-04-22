from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Tag, TagRead, Task, TaskTagLink, User


class TagService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, user: User) -> list[TagRead]:
        stmt = select(Tag).where(Tag.user_id == user.id)
        tags = await self.session.scalars(stmt)
        return [self._to_read(tag) for tag in tags.all()]

    async def create(self, user: User, name: str) -> TagRead:
        if user.id is None:
            raise HTTPException(status_code=500, detail="User ID is missing")

        stmt = select(Tag).where(Tag.user_id == user.id, Tag.name == name)
        existing_tag = (await self.session.scalars(stmt)).first()

        if existing_tag:
            return self._to_read(existing_tag)

        tag = Tag(name=name, user_id=user.id)
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return self._to_read(tag)

    async def rename(self, tag_id: int, user: User, new_name: str) -> TagRead | None:
        stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
        tag = (await self.session.scalars(stmt)).first()

        if not tag:
            return None

        stmt = select(Tag).where(
            Tag.user_id == user.id, Tag.name == new_name, Tag.id != tag_id
        )
        existing_tag = (await self.session.scalars(stmt)).first()

        if existing_tag:
            await self._merge_tags(tag, existing_tag)
            return self._to_read(existing_tag)

        tag.name = new_name
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return self._to_read(tag)

    async def delete(self, tag_id: int, user: User) -> bool:
        stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
        tag = (await self.session.scalars(stmt)).first()

        if not tag:
            return False

        await self.session.delete(tag)
        await self.session.commit()
        return True

    async def add_tag_to_task(
        self, task_id: int, tag_id: int, user: User
    ) -> TagRead | None:
        task_stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
        task = (await self.session.scalars(task_stmt)).first()

        if not task:
            return None

        tag_stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
        tag = (await self.session.scalars(tag_stmt)).first()

        if not tag:
            return None

        link_stmt = select(TaskTagLink).where(
            TaskTagLink.task_id == task_id, TaskTagLink.tag_id == tag_id
        )
        existing_link = (await self.session.scalars(link_stmt)).first()

        if existing_link:
            return self._to_read(tag)

        link = TaskTagLink(task_id=task_id, tag_id=tag_id)
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(tag)
        return self._to_read(tag)

    async def remove_tag_from_task(self, task_id: int, tag_id: int, user: User) -> bool:
        task_stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
        task = (await self.session.scalars(task_stmt)).first()

        if not task:
            return False

        tag_stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
        tag = (await self.session.scalars(tag_stmt)).first()

        if not tag:
            return False

        link_stmt = select(TaskTagLink).where(
            TaskTagLink.task_id == task_id, TaskTagLink.tag_id == tag_id
        )
        link = (await self.session.scalars(link_stmt)).first()

        if link:
            await self.session.delete(link)
            await self.session.commit()

        return True

    async def _merge_tags(self, old_tag: Tag, new_tag: Tag) -> None:
        stmt = select(TaskTagLink).where(TaskTagLink.tag_id == old_tag.id)
        links = (await self.session.scalars(stmt)).all()

        if links:
            task_ids = [link.task_id for link in links]
            existing_stmt = select(TaskTagLink).where(
                TaskTagLink.tag_id == new_tag.id,
                TaskTagLink.task_id.in_(task_ids),  # type: ignore[attr-defined]
            )
            already_linked = {
                link.task_id
                for link in (await self.session.scalars(existing_stmt)).all()
            }

            for link in links:
                if link.task_id not in already_linked:
                    self.session.add(TaskTagLink(task_id=link.task_id, tag_id=new_tag.id))
                await self.session.delete(link)

        await self.session.delete(old_tag)
        await self.session.commit()

    def _to_read(self, tag: Tag) -> TagRead:
        if tag.id is None:
            raise HTTPException(status_code=500, detail="Tag ID is missing")
        return TagRead(id=tag.id, name=tag.name)
