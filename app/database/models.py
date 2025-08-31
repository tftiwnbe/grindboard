from typing import Any

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    __mapper_args__: Any = {"eager_defaults": True}


class Task(Base):
    __tablename__: str = "task"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(index=True)
    description: Mapped[str] = mapped_column(index=True, nullable=True)
    completed: Mapped[bool] = mapped_column(default=False)
