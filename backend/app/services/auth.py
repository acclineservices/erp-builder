"""Authentication workflows built on the P003 identity foundation."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.core.config import settings
from app.core.notifications import development_notifications
from app.core.security import hash_password, new_otp, new_token, token_digest, verify_password
from app.models import AuthToken, AuthenticationMethod, OtpChallenge, SecurityEvent, Session, User

GENERIC_REQUEST_MESSAGE = "If the account can use this method, instructions have been sent."
INVALID_CREDENTIALS_MESSAGE = "Invalid credentials."


def now() -> datetime:
    return datetime.now(timezone.utc)


def is_expired(value: datetime, at: datetime | None = None) -> bool:
    value = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return value <= (at or now())


def record_event(database: DatabaseSession, user: User | None, event_type: str) -> None:
    database.add(SecurityEvent(user=user, event_type=event_type))


def active_user(user: User | None) -> bool:
    return bool(user and user.is_active and user.account_state == "active")


def issue_auth_token(database: DatabaseSession, user: User, purpose: str, hours: int | None = None) -> str:
    issued_at = now()
    for existing in database.scalars(
        select(AuthToken).where(
            AuthToken.user_id == user.id, AuthToken.purpose == purpose, AuthToken.consumed_at.is_(None)
        )
    ):
        existing.consumed_at = issued_at
    value = new_token()
    database.add(
        AuthToken(
            user=user,
            purpose=purpose,
            token_hash=token_digest(value),
            expires_at=issued_at + timedelta(hours=hours or settings.auth_activation_hours),
        )
    )
    return value


def consume_auth_token(database: DatabaseSession, value: str, purpose: str) -> AuthToken | None:
    token = database.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == token_digest(value), AuthToken.purpose == purpose, AuthToken.consumed_at.is_(None)
        )
    )
    if token is None or is_expired(token.expires_at):
        return None
    token.consumed_at = now()
    return token


def issue_otp(database: DatabaseSession, user: User, purpose: str) -> str:
    issued_at = now()
    for existing in database.scalars(
        select(OtpChallenge).where(
            OtpChallenge.user_id == user.id, OtpChallenge.purpose == purpose, OtpChallenge.consumed_at.is_(None)
        )
    ):
        existing.consumed_at = issued_at
    code = new_otp()
    database.add(
        OtpChallenge(
            user=user,
            mobile_number=user.mobile_number or "",
            purpose=purpose,
            code_hash=hash_password(code),
            expires_at=issued_at + timedelta(minutes=settings.auth_otp_minutes),
        )
    )
    development_notifications.deliver(purpose, user.mobile_number or "", code)
    return code


def consume_otp(database: DatabaseSession, mobile_number: str, code: str, purpose: str) -> User | None:
    challenge = database.scalar(
        select(OtpChallenge)
        .where(
            OtpChallenge.mobile_number == mobile_number,
            OtpChallenge.purpose == purpose,
            OtpChallenge.consumed_at.is_(None),
        )
        .order_by(OtpChallenge.created_at.desc())
    )
    if challenge is None or is_expired(challenge.expires_at) or challenge.attempts >= settings.auth_otp_max_attempts:
        return None
    challenge.attempts += 1
    if not verify_password(code, challenge.code_hash):
        if challenge.attempts >= settings.auth_otp_max_attempts:
            challenge.consumed_at = now()
            record_event(database, challenge.user, "otp_attempt_limit")
        return None
    challenge.consumed_at = now()
    return challenge.user


def complete_activation(database: DatabaseSession, token_value: str, password: str) -> bool:
    token = consume_auth_token(database, token_value, "activation")
    if token is None or token.user.account_state != "invited":
        return False
    method = database.scalar(
        select(AuthenticationMethod).where(
            AuthenticationMethod.user_id == token.user_id, AuthenticationMethod.method_type == "email_password"
        )
    )
    if method is None:
        method = AuthenticationMethod(user=token.user, method_type="email_password")
        database.add(method)
    method.credential_hash = hash_password(password)
    method.is_active = True
    method.is_verified = False
    email_token = issue_auth_token(database, token.user, "email_verification")
    development_notifications.deliver("email_verification", token.user.email or "", email_token)
    return True


def verify_email(database: DatabaseSession, token_value: str) -> bool:
    token = consume_auth_token(database, token_value, "email_verification")
    if token is None:
        return False
    token.user.email_verified = True
    email_method = database.scalar(
        select(AuthenticationMethod).where(
            AuthenticationMethod.user_id == token.user_id,
            AuthenticationMethod.method_type == "email_password",
        )
    )
    if email_method:
        email_method.is_verified = True
    activate_if_verified(token.user)
    return True


def verify_mobile(database: DatabaseSession, mobile_number: str, code: str) -> bool:
    user = consume_otp(database, mobile_number, code, "mobile_verification")
    if user is None:
        return False
    user.mobile_verified = True
    mobile_method = database.scalar(
        select(AuthenticationMethod).where(
            AuthenticationMethod.user_id == user.id,
            AuthenticationMethod.method_type == "mobile_otp",
        )
    )
    if mobile_method is None:
        mobile_method = AuthenticationMethod(user=user, method_type="mobile_otp")
        database.add(mobile_method)
    mobile_method.is_active = True
    mobile_method.is_verified = True
    activate_if_verified(user)
    return True


def activate_if_verified(user: User) -> None:
    if user.email_verified and user.mobile_verified and user.is_active:
        user.account_state = "active"
        record_event(object_session(user), user, "account_activated")


def object_session(user: User) -> DatabaseSession:
    """Relationship helper with a narrow type boundary for SQLAlchemy's session lookup."""
    from sqlalchemy.orm import object_session as sqlalchemy_object_session

    session = sqlalchemy_object_session(user)
    assert session is not None
    return session


def request_activation(database: DatabaseSession, email: str) -> None:
    user = database.scalar(select(User).where(User.email == email, User.account_state == "invited", User.is_active.is_(True)))
    if user:
        value = issue_auth_token(database, user, "activation")
        development_notifications.deliver("activation", user.email or "", value)


def request_mobile_otp(database: DatabaseSession, mobile_number: str, purpose: str) -> None:
    user = database.scalar(select(User).where(User.mobile_number == mobile_number))
    mobile_method = (
        database.scalar(
            select(AuthenticationMethod).where(
                AuthenticationMethod.user_id == user.id,
                AuthenticationMethod.method_type == "mobile_otp",
                AuthenticationMethod.is_active.is_(True),
                AuthenticationMethod.is_verified.is_(True),
            )
        )
        if user
        else None
    )
    allowed = bool(user and user.is_active and (
        (user.account_state == "active" and mobile_method)
        or purpose == "mobile_verification" and user.account_state == "invited"
    ))
    if allowed:
        issue_otp(database, user, purpose)


def request_password_reset(database: DatabaseSession, email: str) -> None:
    user = database.scalar(select(User).where(User.email == email))
    if active_user(user):
        value = issue_auth_token(database, user, "password_reset")
        development_notifications.deliver("password_reset", user.email or "", value)


def set_password(database: DatabaseSession, user: User, password: str) -> None:
    method = database.scalar(
        select(AuthenticationMethod).where(
            AuthenticationMethod.user_id == user.id, AuthenticationMethod.method_type == "email_password"
        )
    )
    if method is None:
        method = AuthenticationMethod(user=user, method_type="email_password")
        database.add(method)
    method.credential_hash = hash_password(password)
    method.is_active = True
    for session in database.scalars(select(Session).where(Session.user_id == user.id, Session.revoked_at.is_(None))):
        session.revoked_at = now()


def reset_password(database: DatabaseSession, token_value: str, password: str) -> bool:
    token = consume_auth_token(database, token_value, "password_reset")
    if token is None or not active_user(token.user):
        return False
    set_password(database, token.user, password)
    record_event(database, token.user, "password_reset")
    return True


def reset_password_mobile(database: DatabaseSession, mobile_number: str, code: str, password: str) -> bool:
    user = consume_otp(database, mobile_number, code, "mobile_password_reset")
    if not active_user(user):
        return False
    set_password(database, user, password)
    record_event(database, user, "password_reset_mobile")
    return True


def authenticate_email(database: DatabaseSession, email: str, password: str) -> User | None:
    user = database.scalar(select(User).where(User.email == email))
    if not active_user(user):
        return None
    if user.locked_until and not is_expired(user.locked_until):
        record_event(database, user, "login_blocked_temporary_lock")
        return None
    method = database.scalar(
        select(AuthenticationMethod).where(
            AuthenticationMethod.user_id == user.id,
            AuthenticationMethod.method_type == "email_password",
            AuthenticationMethod.is_active.is_(True),
            AuthenticationMethod.is_verified.is_(True),
        )
    )
    if method is None or not method.credential_hash or not verify_password(password, method.credential_hash):
        user.failed_login_count += 1
        record_event(database, user, "failed_email_login")
        if user.failed_login_count >= settings.auth_failed_login_limit:
            user.locked_until = now() + timedelta(minutes=settings.auth_lock_minutes)
            user.failed_login_count = 0
            record_event(database, user, "temporary_login_lock")
        return None
    user.failed_login_count = 0
    user.locked_until = None
    return user


def create_session(database: DatabaseSession, user: User, remember_me: bool, platform: bool = False) -> tuple[Session, str]:
    value = new_token()
    lifetime = settings.auth_remember_me_minutes if remember_me else settings.auth_session_minutes
    session = Session(
        user=user,
        token_hash=token_digest(value),
        expires_at=now() + timedelta(minutes=lifetime),
        remember_me=remember_me,
        is_platform_session=platform,
    )
    database.add(session)
    return session, value


def authenticated_session(database: DatabaseSession, token_value: str | None, platform: bool = False) -> Session | None:
    if not token_value:
        return None
    session = database.scalar(select(Session).where(Session.token_hash == token_digest(token_value)))
    if session is None or session.revoked_at or is_expired(session.expires_at) or not active_user(session.user):
        return None
    if session.is_platform_session != platform:
        return None
    if platform and not session.user.is_platform_admin:
        return None
    return session


def revoke_session(database: DatabaseSession, token_value: str | None) -> None:
    if token_value:
        session = database.scalar(select(Session).where(Session.token_hash == token_digest(token_value)))
        if session and not session.revoked_at:
            session.revoked_at = now()
