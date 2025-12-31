from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    __mapper_args__: Any = {"eager_defaults": True}


class Task(Base):
    __tablename__: str = "task"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(index=True)
    description: Mapped[str] = mapped_column(index=True, nullable=True)
    completed: Mapped[bool] = mapped_column(default=False)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user: Mapped["User | None"] = relationship(back_populates="tasks")


class User(Base):
    __tablename__: str = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))

    tasks: Mapped[list["Task"]] = relationship(back_populates="user")
