"""P007 company-scoped user, role, permission, and security administration API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DatabaseSession

from app.api.dependencies import AuthorizedCompanyContext, require_authorized_company_context
from app.db.session import get_db
from app.models import Role, UserCompanyAccess
from app.schemas.administration import (
    ActiveStatusRequest,
    AdministrationBootstrapResponse,
    AuditEventResponse,
    CompanyUserResponse,
    PermissionResponse,
    RoleInput,
    RoleResponse,
    UserInviteRequest,
    UserUpdateRequest,
)
from app.schemas.auth import MessageResponse
from app.services import administration as service

router = APIRouter(prefix="/administration", tags=["company administration"])


def fail(error: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN if isinstance(error, service.AdministrationForbidden) else status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error))


def authorize(context: AuthorizedCompanyContext, database: DatabaseSession, permission: str) -> set[str]:
    try:
        return service.require_permission(database, context.user, context.company, permission)
    except (service.AdministrationError, service.AdministrationForbidden) as error:
        raise fail(error) from error


def role_response(role: Role) -> RoleResponse:
    return RoleResponse(id=role.id, name=role.name, description=role.description, is_active=role.is_active, is_system_managed=role.is_system_managed, permission_codes=sorted(item.code for item in role.permissions))


def user_response(database: DatabaseSession, context: AuthorizedCompanyContext, access: UserCompanyAccess) -> CompanyUserResponse:
    roles = service.assignments_for_user(database, context.company.id, access.user_id)
    user = access.user
    return CompanyUserResponse(
        id=user.id, name=user.name, email=user.email or "", mobile_number=user.mobile_number or "", account_state=user.account_state,
        email_verified=user.email_verified, mobile_verified=user.mobile_verified, company_access_active=access.is_active,
        role_ids=[role.id for role in roles], role_names=[role.name for role in roles], default_branch_id=access.default_branch_id,
        default_warehouse_id=access.default_warehouse_id, has_active_session=service.has_active_session(database, user.id),
    )


@router.get("/bootstrap", response_model=AdministrationBootstrapResponse)
def bootstrap(
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> AdministrationBootstrapResponse:
    codes = authorize(context, database, "users.view")
    database.commit()
    return AdministrationBootstrapResponse(
        users=[user_response(database, context, item) for item in service.users_for_company(database, context.company.id)],
        roles=[role_response(role) for role in service.roles_for_company(database, context.company.id)],
        permissions=[PermissionResponse(code=item.code, description=item.description) for item in service.permissions(database)],
        branches=[{"id": str(item.id), "name": item.name, "is_active": item.is_active} for item in context.company.branches],
        warehouses=[{"id": str(item.id), "name": item.name, "branch_id": str(item.branch_id) if item.branch_id else None, "is_active": item.is_active} for item in context.company.warehouses],
        audit_events=[AuditEventResponse.model_validate(item, from_attributes=True) for item in service.audit_events(database, context.company.id)],
        effective_permissions=sorted(codes),
    )


@router.get("/users", response_model=list[CompanyUserResponse])
def list_users(
    search: str | None = None, active: bool | None = None,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> list[CompanyUserResponse]:
    authorize(context, database, "users.view")
    return [user_response(database, context, item) for item in service.users_for_company(database, context.company.id, search, active)]


@router.get("/users/{user_id}", response_model=CompanyUserResponse)
def get_user(
    user_id: UUID, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> CompanyUserResponse:
    authorize(context, database, "users.view")
    access = service.access_for_company_user(database, context.company.id, user_id)
    if access is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The requested user is not available in this company.")
    return user_response(database, context, access)


@router.post("/users", response_model=CompanyUserResponse, status_code=status.HTTP_201_CREATED)
def invite_user(
    payload: UserInviteRequest, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> CompanyUserResponse:
    codes = authorize(context, database, "users.invite")
    try:
        access = service.invite_user(database, context.company, context.user, codes, payload)
        database.commit(); database.refresh(access)
    except (service.AdministrationError, service.AdministrationForbidden) as error:
        database.rollback(); raise fail(error) from error
    except IntegrityError as error:
        database.rollback(); raise HTTPException(status_code=409, detail="An identity or role assignment already exists.") from error
    return user_response(database, context, access)


@router.put("/users/{user_id}", response_model=CompanyUserResponse)
def update_user(
    user_id: UUID, payload: UserUpdateRequest, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> CompanyUserResponse:
    codes = authorize(context, database, "users.manage")
    try:
        access = service.update_user(database, context.company, context.user, codes, user_id, payload)
        database.commit(); database.refresh(access)
    except (service.AdministrationError, service.AdministrationForbidden) as error:
        database.rollback(); raise fail(error) from error
    return user_response(database, context, access)


@router.patch("/users/{user_id}/status", response_model=CompanyUserResponse)
def set_user_status(
    user_id: UUID, payload: ActiveStatusRequest, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> CompanyUserResponse:
    authorize(context, database, "users.manage")
    try:
        access = service.set_user_access_status(database, context.company, context.user, user_id, payload.is_active)
        database.commit(); database.refresh(access)
    except (service.AdministrationError, service.AdministrationForbidden) as error:
        database.rollback(); raise fail(error) from error
    return user_response(database, context, access)


@router.post("/users/{user_id}/force-logout", response_model=MessageResponse)
def force_logout(
    user_id: UUID, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> MessageResponse:
    authorize(context, database, "users.security")
    try:
        service.force_logout(database, context.company, context.user, user_id); database.commit()
    except (service.AdministrationError, service.AdministrationForbidden) as error:
        database.rollback(); raise fail(error) from error
    return MessageResponse(message="Active company-user sessions were ended.")


@router.post("/users/{user_id}/reset", response_model=MessageResponse)
def initiate_reset(
    user_id: UUID, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> MessageResponse:
    authorize(context, database, "users.security")
    try:
        service.initiate_reset(database, context.company, context.user, user_id); database.commit()
    except service.AdministrationError as error:
        database.rollback(); raise fail(error) from error
    return MessageResponse(message="Secure activation or reset instructions have been initiated.")


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleInput, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> RoleResponse:
    codes = authorize(context, database, "roles.manage")
    try:
        role = service.create_role(database, context.company, context.user, codes, payload); database.commit(); database.refresh(role)
    except (service.AdministrationError, service.AdministrationForbidden) as error:
        database.rollback(); raise fail(error) from error
    return role_response(role)


@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: UUID, payload: RoleInput, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> RoleResponse:
    codes = authorize(context, database, "roles.manage")
    try:
        role = service.update_role(database, context.company, context.user, codes, role_id, payload); database.commit(); database.refresh(role)
    except (service.AdministrationError, service.AdministrationForbidden) as error:
        database.rollback(); raise fail(error) from error
    return role_response(role)


@router.post("/roles/{role_id}/clone", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def clone_role(
    role_id: UUID, payload: RoleInput, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
) -> RoleResponse:
    codes = authorize(context, database, "roles.manage")
    try:
        role = service.clone_role(database, context.company, context.user, codes, role_id, payload.name); database.commit(); database.refresh(role)
    except (service.AdministrationError, service.AdministrationForbidden) as error:
        database.rollback(); raise fail(error) from error
    return role_response(role)
