from pydantic import BaseModel, Field, field_validator


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    completed: bool = False


class Task(TaskBase):
    id: int

    class ConfigDict:
        from_attributes: bool = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=6)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("username must not be empty or whitespace")
        if len(stripped) > 20:
            raise ValueError("username must be at most 20 characters")
        return stripped


class TokenOut(BaseModel):
    token: str
