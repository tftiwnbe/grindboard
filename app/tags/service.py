from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Tag, Task, TaskTagLink, User


class TagService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, user: User):
        """Get all tags for a user."""
        stmt = select(Tag).where(Tag.user_id == user.id)
        tags = await self.session.scalars(stmt)
        return tags.all()

    async def create(self, user: User, name: str) -> Tag:
        """Create a new tag for a user."""
        assert user.id is not None, "User must have an ID"

        # Check if tag with this name already exists for this user
        stmt = select(Tag).where(Tag.user_id == user.id, Tag.name == name)
        existing_tag = (await self.session.scalars(stmt)).first()

        if existing_tag:
            return existing_tag

        tag = Tag(name=name, user_id=user.id)
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def rename(self, tag_id: int, user: User, new_name: str) -> Tag | None:
        """Rename a tag."""
        stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
        tag = (await self.session.scalars(stmt)).first()

        if not tag:
            return None

        # Check if another tag with this name already exists
        stmt = select(Tag).where(
            Tag.user_id == user.id, Tag.name == new_name, Tag.id != tag_id
        )
        existing_tag = (await self.session.scalars(stmt)).first()

        if existing_tag:
            # Merge tags: move all tasks from current tag to existing tag
            await self._merge_tags(tag, existing_tag)
            return existing_tag

        tag.name = new_name
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def delete(self, tag_id: int, user: User) -> bool:
        """Delete a tag and remove it from all tasks."""
        stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
        tag = (await self.session.scalars(stmt)).first()

        if not tag:
            return False

        await self.session.delete(tag)
        await self.session.commit()
        return True

    async def add_tag_to_task(
        self, task_id: int, tag_id: int, user: User
    ) -> Tag | None:
        """Add an existing tag to a task."""
        # Verify task belongs to user
        task_stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
        task = (await self.session.scalars(task_stmt)).first()

        if not task:
            return None

        # Verify tag belongs to user
        tag_stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
        tag = (await self.session.scalars(tag_stmt)).first()

        if not tag:
            return None

        # Check if link already exists
        link_stmt = select(TaskTagLink).where(
            TaskTagLink.task_id == task_id, TaskTagLink.tag_id == tag_id
        )
        existing_link = (await self.session.scalars(link_stmt)).first()

        if existing_link:
            return tag

        # Create the link
        link = TaskTagLink(task_id=task_id, tag_id=tag_id)
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def remove_tag_from_task(self, task_id: int, tag_id: int, user: User) -> bool:
        """Remove a tag from a task."""
        # Verify task belongs to user
        task_stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
        task = (await self.session.scalars(task_stmt)).first()

        if not task:
            return False

        # Verify tag belongs to user
        tag_stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
        tag = (await self.session.scalars(tag_stmt)).first()

        if not tag:
            return False

        # Find and delete the link
        link_stmt = select(TaskTagLink).where(
            TaskTagLink.task_id == task_id, TaskTagLink.tag_id == tag_id
        )
        link = (await self.session.scalars(link_stmt)).first()

        if link:
            await self.session.delete(link)
            await self.session.commit()

        return True

    async def create_and_add_to_task(
        self, task_id: int, user: User, name: str
    ) -> Tag | None:
        """Create a new tag and add it to a task, or use existing tag."""
        # Verify task belongs to user
        task_stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
        task = (await self.session.scalars(task_stmt)).first()

        if not task:
            return None

        # Create or get existing tag
        tag = await self.create(user, name)

        # After commit, tag.id is guaranteed to exist
        assert tag.id is not None, "Tag must have an ID after creation"

        # Add tag to task
        await self.add_tag_to_task(task_id, tag.id, user)

        return tag

    async def _merge_tags(self, old_tag: Tag, new_tag: Tag) -> None:
        """Helper method to merge old_tag into new_tag."""
        # Get all task links for old tag
        stmt = select(TaskTagLink).where(TaskTagLink.tag_id == old_tag.id)
        links = (await self.session.scalars(stmt)).all()

        for link in links:
            # Check if new tag already linked to this task
            check_stmt = select(TaskTagLink).where(
                TaskTagLink.task_id == link.task_id, TaskTagLink.tag_id == new_tag.id
            )
            existing = (await self.session.scalars(check_stmt)).first()

            if not existing:
                # Create new link
                new_link = TaskTagLink(task_id=link.task_id, tag_id=new_tag.id)
                self.session.add(new_link)

            # Delete old link
            await self.session.delete(link)

        # Delete old tag
        await self.session.delete(old_tag)
        await self.session.commit()
