from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root: helpdesk-system/
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """
    Central configuration for the Helpdesk application.

    Values are loaded from environment variables or the
    project's root .env file.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = "IT Helpdesk System"
    environment: str = "development"
    debug: bool = True

    # API settings
    api_v1_prefix: str = "/api/v1"

    # Database settings
    database_url: str = "sqlite:///./helpdesk.db"

    # Authentication settings
    secret_key: str = "dev-only-change-this-secret-key"
    access_token_expire_minutes: int = Field(
        default=30,
        gt=0,
    )

    # Frontend origins allowed to access the backend
    cors_origins: list[str] = [
        "http://localhost:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    The configuration is loaded once and reused
    throughout the application.
    """
    return Settings()


# Shared application settings
settings = get_settings()
