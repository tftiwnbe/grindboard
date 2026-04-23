from datetime import date, datetime
from typing import Any, ClassVar

from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel

from app.models.tags import Tag, TagRead, TaskTagLink
from app.models.users import User


class Task(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "tasks"

    id: int = Field(primary_key=True)
    title: str = Field(index=True)
    description: str = Field(default="")
    position: float = Field(default=0.0, index=True)
    completed: bool = Field(default=False)
    completed_at: datetime | None = Field(default=None, nullable=True)
    deadline: date | None = Field(default=None, nullable=True)

    tags: Mapped[list[Tag]] = Relationship(
        back_populates="tasks", link_model=TaskTagLink
    )
    user_id: int = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    user: "User" = Relationship(back_populates="tasks")


class TaskCreate(SQLModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    deadline: date | None = None


class TaskUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    deadline: date | None = None


class TaskRead(SQLModel):
    id: int
    title: str
    description: str
    position: float
    completed: bool
    completed_at: datetime | None
    deadline: date | None
    tags: list[TagRead]
