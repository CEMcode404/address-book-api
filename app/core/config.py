"""Application configuration.

Settings are loaded from environment variables or a local ``.env`` file,
falling back to the defaults defined below.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "Address Book API"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./address_book.db"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()