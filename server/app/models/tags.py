from typing import TYPE_CHECKING, Any, ClassVar

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.tasks import Task
    from app.models.users import User


class TaskTagLink(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "task_tags"

    task_id: int | None = Field(default=None, foreign_key="tasks.id", primary_key=True)
    tag_id: int | None = Field(default=None, foreign_key="tags.id", primary_key=True)


class Tag(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "tags"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    tasks: list["Task"] = Relationship(back_populates="tags", link_model=TaskTagLink)
    user: "User" = Relationship(back_populates="tags")
