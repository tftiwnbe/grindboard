from typing import Any

from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict


class Settings(BaseSettings):
    model_config: Any = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Base
    project_name: str = "Grindboard"
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    echo_sql: bool = False
    log_level: str = "INFO"

    # Auth (JWT)
    token_ttl_minutes: int = 60 * 24  # 24h by default
    jwt_secret_key: str = "change-me"  # override via env for production
    jwt_algorithm: str = "HS256"


settings = Settings()
