"""Shared authenticated request dependencies for non-authentication API areas."""

from dataclasses import dataclass
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DatabaseSession

from app.core.company_context import CompanyContext, CompanyContextAccessError, require_active_company_access
from app.core.config import settings
from app.db.session import get_db
from app.models import Company, User
from app.services import auth as auth_service


def require_authenticated_user(
    session_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
    database: DatabaseSession = Depends(get_db),
) -> User:
    session = auth_service.authenticated_session(database, session_token)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return session.user


@dataclass(frozen=True)
class AuthorizedCompanyContext:
    user: User
    company: Company


def require_authorized_company_context(
    company_id: UUID = Header(alias="X-Company-ID"),
    user: User = Depends(require_authenticated_user),
    database: DatabaseSession = Depends(get_db),
) -> AuthorizedCompanyContext:
    """Require an active UserCompanyAccess grant for the selected company header."""
    try:
        require_active_company_access(database, CompanyContext(user_id=user.id, company_id=company_id))
    except CompanyContextAccessError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company access is not permitted.") from error
    company = database.get(Company, company_id)
    assert company is not None
    return AuthorizedCompanyContext(user=user, company=company)
