import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class GrindboardBaseSettings(BaseSettings):
    """Base settings with shared configuration."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        env_prefix="GRINDBOARD__",
        env_nested_delimiter="__",
        extra="ignore",
    )


class AppConfig(GrindboardBaseSettings):
    project_name: str = "Grindboard"
    data_dir: Path = DATA_DIR
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8000"]
    )
    cors_allow_origin_regex: str | None = None
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.data_dir}/grindboard.db"


class AuthConfig(GrindboardBaseSettings):
    token_ttl_minutes: int = 60 * 24  # 24h by default
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v:
            return secrets.token_urlsafe(32)
        return v


class Settings(GrindboardBaseSettings):
    app: AppConfig = Field(default_factory=AppConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the current settings instance."""
    return Settings()
