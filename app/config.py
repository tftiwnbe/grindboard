import secrets
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

APP_DIR = Path(__file__).resolve().parent
CONFIG_DIR = APP_DIR.parent / "config"


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
    config_dir: Path = CONFIG_DIR
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
    def config_path(self) -> Path:
        return self.config_dir / "config.yaml"

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.config_dir}/grindboard.db"


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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_path = CONFIG_DIR / "config.yaml"
        sources: list[PydanticBaseSettingsSource] = [
            env_settings,
            dotenv_settings,
        ]

        if yaml_path.exists():
            sources.append(
                YamlConfigSettingsSource(
                    settings_cls,
                    yaml_file=yaml_path,
                    yaml_file_encoding="utf-8",
                )
            )

        sources.extend([init_settings, file_secret_settings])
        return tuple(sources)

    def save_settings(self) -> None:
        """Persist settings back to YAML config file."""
        path = self.app.config_path
        data = self.model_dump(exclude={"app"}, mode="json")

        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the current settings instance."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
