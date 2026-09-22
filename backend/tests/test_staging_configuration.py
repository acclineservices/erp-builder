"""Deployment-safe configuration coverage for the P010.1 staging checkpoint."""

import pytest
from fastapi import Response
from pydantic import ValidationError

from app.core.config import Settings, normalize_database_url, settings
from app.api.routes.auth import set_session_cookie
from app.services import auth as auth_service


def test_render_style_postgresql_url_uses_installed_psycopg_driver() -> None:
    url = normalize_database_url("postgresql://user:password@example.com:5432/pruvian")

    assert url == "postgresql+psycopg://user:password@example.com:5432/pruvian"


def test_explicit_postgresql_driver_is_preserved() -> None:
    url = normalize_database_url("postgresql+psycopg://user:password@example.com:5432/pruvian")

    assert url == "postgresql+psycopg://user:password@example.com:5432/pruvian"


def test_credentialed_cors_rejects_a_wildcard_origin() -> None:
    with pytest.raises(ValidationError, match="cannot include"):
        Settings(backend_cors_origins="*")


def test_cross_site_cookie_configuration_requires_https() -> None:
    with pytest.raises(ValidationError, match="must be true"):
        Settings(auth_cookie_samesite="none", auth_cookie_secure=False)

    configured = Settings(auth_cookie_samesite="none", auth_cookie_secure=True, auth_cookie_domain="")
    assert configured.auth_cookie_domain is None


def test_https_cookie_settings_are_applied_to_authentication(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "auth_cookie_secure", True)
    monkeypatch.setattr(settings, "auth_cookie_samesite", "none")
    monkeypatch.setattr(settings, "auth_cookie_domain", ".pruviantechnologies.com")

    response = Response()
    set_session_cookie(response, "opaque-session-token", auth_service.now(), remember_me=False)

    assert "Secure" in response.headers["set-cookie"]
    assert "SameSite=none" in response.headers["set-cookie"]
    assert "Domain=.pruviantechnologies.com" in response.headers["set-cookie"]
