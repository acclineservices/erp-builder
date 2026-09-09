"""HTTP boundary for P004 authentication and authenticated company access."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.core.config import settings
from app.db.session import get_db
from app.models import Company, User, UserCompanyAccess
from app.schemas.auth import (
    ActivationRequest,
    CompanyResponse,
    EmailLoginRequest,
    EmailRequest,
    MessageResponse,
    MobileOtpLoginRequest,
    MobilePasswordResetRequest,
    MobileRequest,
    PasswordResetRequest,
    SessionResponse,
    TokenRequest,
    UserResponse,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])
admin_router = APIRouter(prefix="/admin/auth", tags=["platform authentication"])


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        mobile_number=user.mobile_number,
        account_state=user.account_state,
        is_platform_admin=user.is_platform_admin,
    )


def set_session_cookie(
    response: Response, token: str, expires_at: datetime, remember_me: bool, platform: bool = False
) -> None:
    cookie_name = settings.auth_platform_cookie_name if platform else settings.auth_cookie_name
    seconds = max(1, int((expires_at - auth_service.now()).total_seconds()))
    cookie_options: dict[str, str | int | bool] = {
        "key": cookie_name,
        "value": token,
        "httponly": True,
        "secure": settings.auth_cookie_secure,
        "samesite": "lax",
        "path": "/",
    }
    if remember_me:
        cookie_options["max_age"] = seconds
    response.set_cookie(**cookie_options)


def require_session(
    database: DatabaseSession, token: str | None, platform: bool = False
):
    session = auth_service.authenticated_session(database, token, platform=platform)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return session


@router.post("/login/email", response_model=SessionResponse)
def email_login(payload: EmailLoginRequest, response: Response, database: DatabaseSession = Depends(get_db)) -> SessionResponse:
    user = auth_service.authenticate_email(database, payload.email.lower(), payload.password)
    if user is None:
        database.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=auth_service.INVALID_CREDENTIALS_MESSAGE)
    session, token = auth_service.create_session(database, user, payload.remember_me)
    database.commit()
    set_session_cookie(response, token, session.expires_at, payload.remember_me)
    return SessionResponse(user=user_response(user), expires_at=session.expires_at)


@router.post("/login/mobile/request", response_model=MessageResponse)
def request_mobile_login(payload: MobileRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    auth_service.request_mobile_otp(database, payload.mobile_number, "mobile_login")
    database.commit()
    return MessageResponse(message=auth_service.GENERIC_REQUEST_MESSAGE)


@router.post("/login/mobile/verify", response_model=SessionResponse)
def verify_mobile_login(payload: MobileOtpLoginRequest, response: Response, database: DatabaseSession = Depends(get_db)) -> SessionResponse:
    user = auth_service.consume_otp(database, payload.mobile_number, payload.code, "mobile_login")
    if not auth_service.active_user(user):
        database.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=auth_service.INVALID_CREDENTIALS_MESSAGE)
    session, token = auth_service.create_session(database, user, payload.remember_me)
    database.commit()
    set_session_cookie(response, token, session.expires_at, payload.remember_me)
    return SessionResponse(user=user_response(user), expires_at=session.expires_at)


@router.post("/activation/request", response_model=MessageResponse)
def request_activation(payload: EmailRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    auth_service.request_activation(database, payload.email.lower())
    database.commit()
    return MessageResponse(message=auth_service.GENERIC_REQUEST_MESSAGE)


@router.post("/activation/complete", response_model=MessageResponse)
def complete_activation(payload: ActivationRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    if not auth_service.complete_activation(database, payload.token, payload.password):
        database.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Activation link is invalid or expired.")
    database.commit()
    return MessageResponse(message="Continue with email and mobile verification to activate the account.")


@router.post("/verify/email", response_model=MessageResponse)
def confirm_email(payload: TokenRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    if not auth_service.verify_email(database, payload.token):
        database.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link is invalid or expired.")
    database.commit()
    return MessageResponse(message="Email verified.")


@router.post("/verify/mobile/request", response_model=MessageResponse)
def request_mobile_verification(payload: MobileRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    auth_service.request_mobile_otp(database, payload.mobile_number, "mobile_verification")
    database.commit()
    return MessageResponse(message=auth_service.GENERIC_REQUEST_MESSAGE)


@router.post("/verify/mobile", response_model=MessageResponse)
def confirm_mobile(payload: MobileOtpLoginRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    if not auth_service.verify_mobile(database, payload.mobile_number, payload.code):
        database.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code is invalid or expired.")
    database.commit()
    return MessageResponse(message="Mobile verified.")


@router.post("/password/forgot", response_model=MessageResponse)
def forgot_password(payload: EmailRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    auth_service.request_password_reset(database, payload.email.lower())
    database.commit()
    return MessageResponse(message=auth_service.GENERIC_REQUEST_MESSAGE)


@router.post("/password/reset", response_model=MessageResponse)
def password_reset(payload: PasswordResetRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    if not auth_service.reset_password(database, payload.token, payload.new_password):
        database.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link is invalid or expired.")
    database.commit()
    return MessageResponse(message="Password reset.")


@router.post("/password/mobile/request", response_model=MessageResponse)
def request_mobile_password_reset(payload: MobileRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    auth_service.request_mobile_otp(database, payload.mobile_number, "mobile_password_reset")
    database.commit()
    return MessageResponse(message=auth_service.GENERIC_REQUEST_MESSAGE)


@router.post("/password/mobile/reset", response_model=MessageResponse)
def mobile_password_reset(payload: MobilePasswordResetRequest, database: DatabaseSession = Depends(get_db)) -> MessageResponse:
    if not auth_service.reset_password_mobile(database, payload.mobile_number, payload.code, payload.new_password):
        database.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset code is invalid or expired.")
    database.commit()
    return MessageResponse(message="Password reset.")


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
    database: DatabaseSession = Depends(get_db),
) -> MessageResponse:
    auth_service.revoke_session(database, session_token)
    database.commit()
    response.delete_cookie(settings.auth_cookie_name, path="/")
    return MessageResponse(message="Signed out.")


@router.get("/me", response_model=SessionResponse)
def current_user(
    session_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
    database: DatabaseSession = Depends(get_db),
) -> SessionResponse:
    session = require_session(database, session_token)
    return SessionResponse(user=user_response(session.user), expires_at=session.expires_at)


@router.get("/companies", response_model=list[CompanyResponse])
def accessible_companies(
    session_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
    database: DatabaseSession = Depends(get_db),
) -> list[CompanyResponse]:
    session = require_session(database, session_token)
    companies = database.scalars(
        select(Company)
        .join(UserCompanyAccess)
        .where(
            UserCompanyAccess.user_id == session.user_id,
            UserCompanyAccess.is_active.is_(True),
            Company.is_active.is_(True),
        )
        .order_by(Company.business_name)
    ).all()
    return [CompanyResponse(id=company.id, business_name=company.business_name) for company in companies]


@admin_router.post("/login", response_model=SessionResponse)
def platform_login(payload: EmailLoginRequest, response: Response, database: DatabaseSession = Depends(get_db)) -> SessionResponse:
    user = auth_service.authenticate_email(database, payload.email.lower(), payload.password)
    if user is None or not user.is_platform_admin:
        database.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=auth_service.INVALID_CREDENTIALS_MESSAGE)
    session, token = auth_service.create_session(database, user, payload.remember_me, platform=True)
    database.commit()
    set_session_cookie(response, token, session.expires_at, payload.remember_me, platform=True)
    return SessionResponse(user=user_response(user), expires_at=session.expires_at)


@admin_router.post("/logout", response_model=MessageResponse)
def platform_logout(
    response: Response,
    platform_token: str | None = Cookie(default=None, alias=settings.auth_platform_cookie_name),
    database: DatabaseSession = Depends(get_db),
) -> MessageResponse:
    auth_service.revoke_session(database, platform_token)
    database.commit()
    response.delete_cookie(settings.auth_platform_cookie_name, path="/")
    return MessageResponse(message="Signed out.")


@admin_router.get("/me", response_model=SessionResponse)
def current_platform_user(
    platform_token: str | None = Cookie(default=None, alias=settings.auth_platform_cookie_name),
    database: DatabaseSession = Depends(get_db),
) -> SessionResponse:
    session = require_session(database, platform_token, platform=True)
    return SessionResponse(user=user_response(session.user), expires_at=session.expires_at)
