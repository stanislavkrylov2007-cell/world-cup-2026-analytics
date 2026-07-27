"""Application configuration utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import URL


@dataclass(frozen=True)
class AppConfig:
    """Application settings loaded from environment variables."""

    app_env: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    @property
    def database_url(self) -> "URL":
        """Build a SQLAlchemy database URL for PostgreSQL."""
        from sqlalchemy import URL

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    def masked_database_url(self) -> str:
        """Return the SQLAlchemy database URL with the password hidden."""
        return self.database_url.render_as_string(hide_password=True)


def _get_required_env(name: str) -> str:
    """Read a required environment variable and raise a clear error if missing."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ValueError(f"Required environment variable '{name}' is not set.")
    return value


def load_config() -> AppConfig:
    """Load application configuration from environment variables."""
    return AppConfig(
        app_env=os.getenv("APP_ENV", "dev"),
        db_host=_get_required_env("DB_HOST"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=_get_required_env("DB_NAME"),
        db_user=_get_required_env("DB_USER"),
        db_password=_get_required_env("DB_PASSWORD"),
    )
