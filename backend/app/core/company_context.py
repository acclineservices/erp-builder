"""Company-context primitives for future authenticated API endpoints."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import User
from app.models.organization import Company, UserCompanyAccess


class CompanyContextAccessError(PermissionError):
    """Raised when a user cannot operate in a requested company context."""


@dataclass(frozen=True)
class CompanyContext:
    """The authenticated user and active company that scope a future request."""

    user_id: UUID
    company_id: UUID


def require_active_company_access(session: Session, context: CompanyContext) -> UserCompanyAccess:
    """Return valid active access or reject a context outside the user's active company grants."""
    access = session.scalar(
        select(UserCompanyAccess)
        .join(UserCompanyAccess.user)
        .join(UserCompanyAccess.company)
        .where(
            UserCompanyAccess.user_id == context.user_id,
            UserCompanyAccess.company_id == context.company_id,
            UserCompanyAccess.is_active.is_(True),
            User.is_active.is_(True),
            Company.is_active.is_(True),
        )
    )
    if access is None:
        raise CompanyContextAccessError("The user does not have active access to this company.")
    return access