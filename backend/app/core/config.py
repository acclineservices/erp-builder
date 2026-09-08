"""Environment-based application configuration."""

from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ERP Builder API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, ge=1, le=65535)
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    postgres_db: str = "erp_builder"
    postgres_user: str = "erp_builder"
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    database_url: str | None = None

    @cached_property
    def cors_origins(self) -> list[str]:
        """Return explicitly configured browser origins for the API."""
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @cached_property
    def sqlalchemy_database_url(self) -> str:
        """Return the explicit database URL or build one from PostgreSQL settings."""
        if self.database_url:
            return self.database_url

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)


settings = Settings()
