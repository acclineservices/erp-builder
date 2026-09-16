"""Company-scoped user, role, permission, and security administration contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PermissionResponse(BaseModel):
    code: str
    description: str | None


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    is_system_managed: bool
    permission_codes: list[str]


class RoleInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    permission_codes: list[str] = Field(default_factory=list)
    is_active: bool = True


class CompanyUserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    mobile_number: str
    account_state: str
    email_verified: bool
    mobile_verified: bool
    company_access_active: bool
    role_ids: list[UUID]
    role_names: list[str]
    default_branch_id: UUID | None
    default_warehouse_id: UUID | None
    has_active_session: bool


class UserInviteRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=3, max_length=320)
    mobile_number: str = Field(min_length=6, max_length=20)
    role_ids: list[UUID] = Field(min_length=1)
    default_branch_id: UUID | None = None
    default_warehouse_id: UUID | None = None


class UserUpdateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    role_ids: list[UUID] = Field(default_factory=list)
    default_branch_id: UUID | None = None
    default_warehouse_id: UUID | None = None


class ActiveStatusRequest(BaseModel):
    is_active: bool


class AuditEventResponse(BaseModel):
    id: UUID
    action: str
    actor_user_id: UUID | None
    target_user_id: UUID | None
    details: str | None
    created_at: datetime


class AdministrationBootstrapResponse(BaseModel):
    users: list[CompanyUserResponse]
    roles: list[RoleResponse]
    permissions: list[PermissionResponse]
    branches: list[dict[str, object]]
    warehouses: list[dict[str, object]]
    audit_events: list[AuditEventResponse]
    effective_permissions: list[str]
