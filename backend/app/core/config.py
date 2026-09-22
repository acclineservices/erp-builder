"""Environment-based application configuration."""

from functools import cached_property

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url


def normalize_database_url(database_url: str) -> str:
    """Make a PostgreSQL URL use the installed psycopg 3 SQLAlchemy driver.

    Render provides standard ``postgresql://`` URLs.  SQLAlchemy otherwise
    interprets that scheme as the psycopg2 driver, which this project does not
    install.  Explicit driver names remain untouched for local compatibility.
    """
    parsed_url = make_url(database_url)
    if parsed_url.drivername in {"postgres", "postgresql"}:
        parsed_url = parsed_url.set(drivername="postgresql+psycopg")
    return parsed_url.render_as_string(hide_password=False)


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Pruvian API"
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

    auth_session_minutes: int = Field(default=480, ge=5, le=43200)
    auth_remember_me_minutes: int = Field(default=43200, ge=60, le=525600)
    auth_otp_minutes: int = Field(default=5, ge=1, le=30)
    auth_otp_max_attempts: int = Field(default=5, ge=1, le=10)
    auth_activation_hours: int = Field(default=24, ge=1, le=168)
    auth_failed_login_limit: int = Field(default=5, ge=1, le=20)
    auth_lock_minutes: int = Field(default=15, ge=1, le=1440)
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    auth_cookie_domain: str | None = None
    auth_cookie_name: str = "erp_builder_session"
    auth_platform_cookie_name: str = "erp_builder_platform_session"

    @field_validator("backend_cors_origins")
    @classmethod
    def cors_origins_must_be_explicit(cls, value: str) -> str:
        """Prevent insecure wildcard origins with credentialed browser requests."""
        if "*" in {origin.strip() for origin in value.split(",")}:
            raise ValueError("BACKEND_CORS_ORIGINS cannot include '*' when credentials are enabled.")
        return value

    @field_validator("auth_cookie_samesite")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("AUTH_COOKIE_SAMESITE must be lax, strict, or none.")
        return normalized

    @field_validator("auth_cookie_domain", mode="before")
    @classmethod
    def empty_cookie_domain_is_host_only(cls, value: str | None) -> str | None:
        return value.strip() or None if isinstance(value, str) else value

    @model_validator(mode="after")
    def cross_site_cookies_require_https(self) -> "Settings":
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("AUTH_COOKIE_SECURE must be true when AUTH_COOKIE_SAMESITE=none.")
        return self

    @cached_property
    def cors_origins(self) -> list[str]:
        """Return explicitly configured browser origins for the API."""
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @cached_property
    def sqlalchemy_database_url(self) -> str:
        """Return the explicit database URL or build one from PostgreSQL settings."""
        if self.database_url:
            return normalize_database_url(self.database_url)

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)


settings = Settings()
