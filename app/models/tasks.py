from typing import Any, ClassVar, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.users import User


class Task(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "tasks"

    id: int = Field(primary_key=True)
    title: str = Field(index=True)
    description: str = Field(default="")
    position: float = Field(default=0.0, index=True)
    completed: bool = Field(default=False)

    user_id: int = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    user: "User" = Relationship(back_populates="tasks")


class TaskCreate(SQLModel):
    title: str
    description: str = ""


class TaskUpdate(SQLModel):
    title: str | None = None
    description: str | None = None


class TaskRead(SQLModel):
    id: int
    title: str
    description: str
    completed: bool
    user_id: int
