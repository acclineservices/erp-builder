"""Persistent domain models.

Import models here so Alembic can reliably discover the shared metadata.
"""

from app.models.identity import AuthToken, AuthenticationMethod, OtpChallenge, Permission, Role, RoleAssignment, SecurityEvent, Session, User, UserManagementAuditEvent
from app.models.organization import Branch, Company, UserCompanyAccess, Warehouse
from app.models.party import Party, PartyAddress, PartyCodeSequence, PartyContact
from app.models.item import Item, ItemCategory, ItemCodeSequence

__all__ = [
    "AuthenticationMethod",
    "AuthToken",
    "Branch",
    "Company",
    "OtpChallenge",
    "Permission",
    "Party",
    "PartyAddress",
    "PartyCodeSequence",
    "PartyContact",
    "Role",
    "RoleAssignment",
    "SecurityEvent",
    "Session",
    "User",
    "UserCompanyAccess",
    "UserManagementAuditEvent",
    "Warehouse",
]
