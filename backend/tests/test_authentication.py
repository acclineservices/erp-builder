"""Deterministic P004 authentication and access-control tests."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.notifications import development_notifications
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import AuthToken, AuthenticationMethod, Company, OtpChallenge, Session as AuthSession, User, UserCompanyAccess
from app.services import auth as auth_service


@pytest.fixture
def database() -> Session:
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(database: Session):
    def override_db():
        yield database

    app.dependency_overrides[get_db] = override_db
    development_notifications.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    development_notifications.clear()


def make_user(database: Session, **overrides: object) -> User:
    values: dict[str, object] = {
        "name": "Auth User",
        "email": "auth@example.com",
        "mobile_number": "+919876543210",
        "account_state": "active",
        "email_verified": True,
        "mobile_verified": True,
    }
    values.update(overrides)
    user = User(**values)
    database.add(user)
    database.flush()
    database.add(
        AuthenticationMethod(
            user=user,
            method_type="email_password",
            credential_hash=hash_password("correct-password"),
            is_verified=True,
        )
    )
    database.add(AuthenticationMethod(user=user, method_type="mobile_otp", is_verified=True))
    database.commit()
    return user


def test_valid_email_password_login_and_logout_invalidates_session(client: TestClient, database: Session) -> None:
    user = make_user(database)
    response = client.post("/auth/login/email", json={"email": user.email, "password": "correct-password"})

    assert response.status_code == 200
    assert "correct-password" not in response.text
    assert client.get("/auth/me").status_code == 200
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_remember_me_controls_cookie_persistence(client: TestClient, database: Session) -> None:
    user = make_user(database)
    regular = client.post("/auth/login/email", json={"email": user.email, "password": "correct-password"})
    assert "Max-Age" not in regular.headers["set-cookie"]
    remembered = client.post(
        "/auth/login/email", json={"email": user.email, "password": "correct-password", "remember_me": True}
    )
    assert "Max-Age" in remembered.headers["set-cookie"]


def test_invalid_and_inactive_credentials_are_generic(client: TestClient, database: Session) -> None:
    active = make_user(database)
    response = client.post("/auth/login/email", json={"email": active.email, "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == auth_service.INVALID_CREDENTIALS_MESSAGE

    inactive = make_user(database, email="inactive@example.com", mobile_number="+919876543211", is_active=False)
    response = client.post("/auth/login/email", json={"email": inactive.email, "password": "correct-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == auth_service.INVALID_CREDENTIALS_MESSAGE

    deactivated = make_user(
        database,
        email="deactivated@example.com",
        mobile_number="+919876543214",
        account_state="inactive",
    )
    response = client.post("/auth/login/email", json={"email": deactivated.email, "password": "correct-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == auth_service.INVALID_CREDENTIALS_MESSAGE


def test_mobile_otp_login_and_limited_attempts(client: TestClient, database: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    user = make_user(database)
    monkeypatch.setattr(settings, "auth_otp_max_attempts", 2)
    client.post("/auth/login/mobile/request", json={"mobile_number": user.mobile_number})
    challenge = database.query(OtpChallenge).one()
    assert challenge.code_hash != "123456"
    assert "123456" not in client.post("/auth/login/mobile/request", json={"mobile_number": user.mobile_number}).text

    for _ in range(2):
        response = client.post("/auth/login/mobile/verify", json={"mobile_number": user.mobile_number, "code": "000000"})
        assert response.status_code == 401
    assert database.query(OtpChallenge).order_by(OtpChallenge.created_at).first().consumed_at is not None

    client.post("/auth/login/mobile/request", json={"mobile_number": user.mobile_number})
    code = development_notifications.messages()[-1].value
    assert client.post("/auth/login/mobile/verify", json={"mobile_number": user.mobile_number, "code": code}).status_code == 200


def test_expired_otp_cannot_authenticate(client: TestClient, database: Session) -> None:
    user = make_user(database)
    client.post("/auth/login/mobile/request", json={"mobile_number": user.mobile_number})
    challenge = database.query(OtpChallenge).one()
    challenge.expires_at = auth_service.now() - timedelta(seconds=1)
    database.commit()
    code = development_notifications.messages()[-1].value
    assert client.post("/auth/login/mobile/verify", json={"mobile_number": user.mobile_number, "code": code}).status_code == 401


def test_activation_requires_unexpired_token_and_both_verifications(client: TestClient, database: Session) -> None:
    invited = make_user(
        database,
        email="invited@example.com",
        mobile_number="+919876543212",
        account_state="invited",
        email_verified=False,
        mobile_verified=False,
    )
    activation = auth_service.issue_auth_token(database, invited, "activation")
    database.commit()
    assert client.post("/auth/activation/complete", json={"token": activation, "password": "new-password"}).status_code == 200
    email_token = development_notifications.messages()[-1].value
    assert client.post("/auth/verify/email", json={"token": email_token}).status_code == 200
    assert invited.account_state == "invited"
    client.post("/auth/verify/mobile/request", json={"mobile_number": invited.mobile_number})
    code = development_notifications.messages()[-1].value
    assert client.post("/auth/verify/mobile", json={"mobile_number": invited.mobile_number, "code": code}).status_code == 200
    assert invited.account_state == "active"

    expired = auth_service.issue_auth_token(database, invited, "activation")
    token = database.query(AuthToken).filter_by(token_hash=auth_service.token_digest(expired)).one()
    token.expires_at = auth_service.now() - timedelta(seconds=1)
    database.commit()
    assert client.post("/auth/activation/complete", json={"token": expired, "password": "another-password"}).status_code == 400


def test_email_and_mobile_password_reset_and_expiry(client: TestClient, database: Session) -> None:
    user = make_user(database)
    client.post("/auth/password/forgot", json={"email": user.email})
    token = development_notifications.messages()[-1].value
    assert client.post("/auth/password/reset", json={"token": token, "new_password": "replacement-password"}).status_code == 200
    assert client.post("/auth/login/email", json={"email": user.email, "password": "replacement-password"}).status_code == 200

    client.post("/auth/password/mobile/request", json={"mobile_number": user.mobile_number})
    code = development_notifications.messages()[-1].value
    assert client.post("/auth/password/mobile/reset", json={"mobile_number": user.mobile_number, "code": code, "new_password": "mobile-reset-password"}).status_code == 200
    assert client.post("/auth/login/email", json={"email": user.email, "password": "mobile-reset-password"}).status_code == 200

    expired = auth_service.issue_auth_token(database, user, "password_reset")
    token_row = database.query(AuthToken).filter_by(token_hash=auth_service.token_digest(expired)).one()
    token_row.expires_at = auth_service.now() - timedelta(seconds=1)
    database.commit()
    assert client.post("/auth/password/reset", json={"token": expired, "new_password": "should-not-work"}).status_code == 400


def test_remember_me_session_timeout_and_failed_login_lock(client: TestClient, database: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    user = make_user(database)
    normal, _ = auth_service.create_session(database, user, False)
    remembered, _ = auth_service.create_session(database, user, True)
    assert remembered.expires_at > normal.expires_at
    normal.expires_at = auth_service.now() - timedelta(seconds=1)
    database.commit()
    assert auth_service.authenticated_session(database, "not-a-session") is None

    monkeypatch.setattr(settings, "auth_failed_login_limit", 2)
    for _ in range(2):
        client.post("/auth/login/email", json={"email": user.email, "password": "wrong-password"})
    database.refresh(user)
    assert user.locked_until is not None
    assert client.post("/auth/login/email", json={"email": user.email, "password": "correct-password"}).status_code == 401


def test_authenticated_company_access_and_platform_boundary(client: TestClient, database: Session) -> None:
    user = make_user(database)
    permitted = Company(business_name="Permitted")
    excluded = Company(business_name="Excluded")
    database.add_all([permitted, excluded, UserCompanyAccess(user=user, company=permitted)])
    database.commit()
    client.post("/auth/login/email", json={"email": user.email, "password": "correct-password"})
    assert client.get("/auth/companies").json() == [{"id": str(permitted.id), "business_name": "Permitted"}]
    assert client.post("/admin/auth/login", json={"email": user.email, "password": "correct-password"}).status_code == 401

    admin = make_user(database, email="admin@example.com", mobile_number="+919876543213", is_platform_admin=True)
    assert client.post("/admin/auth/login", json={"email": admin.email, "password": "correct-password"}).status_code == 200
    assert client.get("/admin/auth/me").status_code == 200
    assert client.post("/admin/auth/logout").status_code == 200
    assert client.get("/admin/auth/me").status_code == 401


def test_standard_responses_do_not_leak_credentials_or_tokens(client: TestClient, database: Session) -> None:
    user = make_user(database)
    response = client.post("/auth/password/forgot", json={"email": user.email})
    delivered_token = development_notifications.messages()[-1].value
    assert delivered_token not in response.text
    assert "password" not in response.text.lower()
    assert client.get("/auth/development/messages").status_code == 404
