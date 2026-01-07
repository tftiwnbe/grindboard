from typing import Any, ClassVar, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from pydantic import field_validator

if TYPE_CHECKING:
    from app.models.tasks import Task


class User(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=150)
    password_hash: str = Field(max_length=256)

    tasks: list["Task"] = Relationship(back_populates="user", cascade_delete=True)


class UserCreate(SQLModel):
    username: str
    password: str


class UserUpdate(SQLModel):
    username: str | None = None
    password: str | None = None


class UserRead(SQLModel):
    id: int
    username: str


class UserLogin(SQLModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("username must not be empty or whitespace")
        if len(trimmed) > 150:
            raise ValueError("username must be at most 150 characters")
        return trimmed

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("password must be at least 6 characters")
        return value


class TokenOut(SQLModel):
    token: str
