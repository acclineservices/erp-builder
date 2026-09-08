"""Persistent domain models.

Import models here so Alembic can reliably discover the shared metadata.
"""

from app.models.identity import AuthenticationMethod, Permission, Role, RoleAssignment, User
from app.models.organization import Branch, Company, UserCompanyAccess, Warehouse

__all__ = [
    "AuthenticationMethod",
    "Branch",
    "Company",
    "Permission",
    "Role",
    "RoleAssignment",
    "User",
    "UserCompanyAccess",
    "Warehouse",
]
