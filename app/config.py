from typing import Any

from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict


class Settings(BaseSettings):
    model_config: Any = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    project_name: str = "Grindboard"
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    echo_sql: bool = True
    log_level: str = "INFO"


settings = Settings()
