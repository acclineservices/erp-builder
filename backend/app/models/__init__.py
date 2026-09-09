"""Persistent domain models.

Import models here so Alembic can reliably discover the shared metadata.
"""

from app.models.identity import AuthToken, AuthenticationMethod, OtpChallenge, Permission, Role, RoleAssignment, SecurityEvent, Session, User
from app.models.organization import Branch, Company, UserCompanyAccess, Warehouse

__all__ = [
    "AuthenticationMethod",
    "AuthToken",
    "Branch",
    "Company",
    "OtpChallenge",
    "Permission",
    "Role",
    "RoleAssignment",
    "SecurityEvent",
    "Session",
    "User",
    "UserCompanyAccess",
    "Warehouse",
]
