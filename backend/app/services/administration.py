"""P007 company-scoped administration and authorization services.

Role assignments are company-wide in this first version. Branch and warehouse
defaults are convenience context only; they are deliberately not authorization
scope constraints.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.notifications import development_notifications
from app.models import (
    Branch,
    Company,
    Permission,
    Role,
    RoleAssignment,
    Session as AuthSession,
    User,
    UserCompanyAccess,
    UserManagementAuditEvent,
    Warehouse,
)
from app.schemas.administration import RoleInput, UserInviteRequest, UserUpdateRequest
from app.services import auth as auth_service


PERMISSION_CATALOGUE = {
    "users.view": "View company users and their safe account status.",
    "users.invite": "Invite a user to this company.",
    "users.manage": "Edit company user roles, defaults, and company access status.",
    "users.security": "Initiate reset or end another company user's sessions.",
    "roles.view": "View company role definitions and permissions.",
    "roles.manage": "Create, edit, clone, and activate custom company roles.",
    "permissions.view": "View the extensible permission catalogue.",
    "customers.view": "View company customers.", "customers.create": "Create company customers.", "customers.edit": "Edit company customers.", "customers.deactivate": "Activate or deactivate company customers.",
    "suppliers.view": "View company suppliers.", "suppliers.create": "Create company suppliers.", "suppliers.edit": "Edit company suppliers.", "suppliers.deactivate": "Activate or deactivate company suppliers.",
    "items.view": "View company item masters.", "items.create": "Create company items and categories.", "items.edit": "Edit company items and categories.", "items.deactivate": "Activate or deactivate company items and categories.",
    "sales.view": "View future sales records.", "sales.create": "Create future sales records.", "sales.edit": "Edit future sales records.", "sales.cancel": "Cancel future sales records.", "sales.export": "Export future sales records.", "sales.approve": "Approve future sales records.",
    "purchases.view": "View future purchase records.", "purchases.create": "Create future purchase records.", "purchases.edit": "Edit future purchase records.", "purchases.cancel": "Cancel future purchase records.", "purchases.export": "Export future purchase records.", "purchases.approve": "Approve future purchase records.",
    "inventory.view": "View future inventory records.", "inventory.create": "Create future inventory records.", "inventory.edit": "Edit future inventory records.", "inventory.approve": "Approve future inventory adjustments.",
    "accounting.view": "View future accounting records.", "accounting.create": "Create future accounting records.", "accounting.edit": "Edit future accounting records.", "accounting.export": "Export future accounting records.", "accounting.approve": "Approve future accounting actions.",
    "reports.view": "View future reports.", "reports.export": "Export future reports.",
}

ALL_PERMISSIONS = frozenset(PERMISSION_CATALOGUE)
STANDARD_ROLE_PERMISSIONS = {
    "Owner": ALL_PERMISSIONS,
    "Admin": ALL_PERMISSIONS,
    "Accountant": frozenset(code for code in ALL_PERMISSIONS if code.startswith(("accounting.", "reports.", "customers.", "suppliers.", "items.", "purchases."))),
    "Sales User": frozenset(code for code in ALL_PERMISSIONS if code.startswith(("sales.", "customers.", "items.view")) and not code.endswith("approve")),
    "Purchase User": frozenset(code for code in ALL_PERMISSIONS if code.startswith(("purchases.", "suppliers.", "items.view")) and not code.endswith("approve")),
    "Inventory User": frozenset(code for code in ALL_PERMISSIONS if code.startswith(("inventory.", "items.")) and not code.endswith("approve")),
    "Store Manager": frozenset(code for code in ALL_PERMISSIONS if code.startswith(("inventory.", "items."))),
    "Viewer": frozenset(code for code in ALL_PERMISSIONS if code.endswith(".view")),
}


class AdministrationError(ValueError):
    pass


class AdministrationForbidden(PermissionError):
    pass


def ensure_company_catalogue(database: Session, company: Company) -> bool:
    """Idempotently seed global permission codes and fixed roles.

    Permission checks run concurrently for a workspace's initial requests. Lock
    the company row while a catalogue upgrade is needed and do not rewrite an
    unchanged role-permission collection on ordinary reads.
    """
    database.scalar(select(Company).where(Company.id == company.id).with_for_update())
    changed = False
    existing_permissions = {item.code: item for item in database.scalars(select(Permission)).all()}
    for code, description in PERMISSION_CATALOGUE.items():
        permission = existing_permissions.get(code)
        if permission is None:
            permission = Permission(code=code, description=description)
            database.add(permission)
            existing_permissions[code] = permission
            changed = True
        elif permission.description != description:
            permission.description = description
            changed = True
    database.flush()
    permissions = {item.code: item for item in database.scalars(select(Permission)).all()}
    existing_roles = {
        item.name: item
        for item in database.scalars(select(Role).where(Role.company_id == company.id)).all()
    }
    for name, codes in STANDARD_ROLE_PERMISSIONS.items():
        role = existing_roles.get(name)
        if role is None:
            role = Role(name=name, scope="company", company_id=company.id, is_system_managed=True)
            database.add(role)
            changed = True
        description = f"System-managed {name} role."
        if role.description != description:
            role.description = description
            changed = True
        if not role.is_system_managed:
            role.is_system_managed = True
            changed = True
        current_codes = {permission.code for permission in role.permissions}
        if current_codes != set(codes):
            role.permissions = [permissions[code] for code in sorted(codes)]
            changed = True
    if changed:
        database.flush()
    return changed


def effective_permission_codes(database: Session, user_id: UUID, company_id: UUID) -> set[str]:
    return set(database.scalars(
        select(Permission.code)
        .join(Permission.roles)
        .join(Role.assignments)
        .where(
            RoleAssignment.user_id == user_id,
            RoleAssignment.company_id == company_id,
            Role.company_id == company_id,
            Role.is_active.is_(True),
        )
    ).all())


def require_permission(database: Session, actor: User, company: Company, permission: str) -> set[str]:
    # Persist a one-time catalogue upgrade before serving concurrent workspace
    # requests; otherwise request-session close would roll it back and retry it.
    if ensure_company_catalogue(database, company):
        database.commit()
    codes = effective_permission_codes(database, actor.id, company.id)
    if permission not in codes:
        raise AdministrationForbidden("You do not have permission for this company administration action.")
    return codes


def roles_for_company(database: Session, company_id: UUID) -> list[Role]:
    return list(database.scalars(select(Role).where(Role.company_id == company_id).order_by(Role.is_system_managed.desc(), Role.name)).all())


def permissions(database: Session) -> list[Permission]:
    return list(database.scalars(select(Permission).order_by(Permission.code)).all())


def access_for_company_user(database: Session, company_id: UUID, user_id: UUID) -> UserCompanyAccess | None:
    return database.scalar(select(UserCompanyAccess).where(UserCompanyAccess.company_id == company_id, UserCompanyAccess.user_id == user_id))


def users_for_company(database: Session, company_id: UUID, search: str | None = None, active: bool | None = None) -> list[UserCompanyAccess]:
    query = select(UserCompanyAccess).join(UserCompanyAccess.user).where(UserCompanyAccess.company_id == company_id)
    if active is not None:
        query = query.where(UserCompanyAccess.is_active.is_(active))
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(User.name.ilike(pattern) | User.email.ilike(pattern) | User.mobile_number.ilike(pattern))
    return list(database.scalars(query.order_by(User.name)).all())


def assignments_for_user(database: Session, company_id: UUID, user_id: UUID) -> list[Role]:
    return list(database.scalars(
        select(Role).join(RoleAssignment).where(
            RoleAssignment.user_id == user_id,
            RoleAssignment.company_id == company_id,
            Role.company_id == company_id,
        ).order_by(Role.name)
    ).all())


def has_active_session(database: Session, user_id: UUID) -> bool:
    return database.scalar(select(AuthSession.id).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))) is not None


def audit(database: Session, company_id: UUID, actor: User, action: str, target: User | None = None, details: str | None = None) -> None:
    database.add(UserManagementAuditEvent(company_id=company_id, actor_user_id=actor.id, target_user_id=target.id if target else None, action=action, details=details))


def validate_defaults(database: Session, company_id: UUID, branch_id: UUID | None, warehouse_id: UUID | None) -> None:
    branch = database.get(Branch, branch_id) if branch_id else None
    warehouse = database.get(Warehouse, warehouse_id) if warehouse_id else None
    if branch and branch.company_id != company_id:
        raise AdministrationError("The default branch is not available in this company.")
    if warehouse and warehouse.company_id != company_id:
        raise AdministrationError("The default warehouse is not available in this company.")
    if branch_id and branch is None:
        raise AdministrationError("The default branch is not available in this company.")
    if warehouse_id and warehouse is None:
        raise AdministrationError("The default warehouse is not available in this company.")
    if warehouse and warehouse.branch_id and warehouse.branch_id != branch_id:
        raise AdministrationError("A warehouse linked to a branch requires that same default branch.")


def selectable_roles(database: Session, company_id: UUID, role_ids: list[UUID], actor_codes: set[str]) -> list[Role]:
    roles = list(database.scalars(select(Role).where(Role.id.in_(role_ids), Role.company_id == company_id, Role.is_active.is_(True))).all()) if role_ids else []
    if len(roles) != len(set(role_ids)):
        raise AdministrationError("One or more selected roles are not available in this company.")
    if any(role.name == "Owner" and role.is_system_managed for role in roles):
        raise AdministrationForbidden("Primary Owner assignments are controlled by Pruvian Technologies.")
    allowed = actor_codes
    for role in roles:
        role_codes = {permission.code for permission in role.permissions}
        if not role_codes.issubset(allowed):
            raise AdministrationForbidden("You cannot grant permissions you do not possess.")
    return roles


def invite_user(database: Session, company: Company, actor: User, actor_codes: set[str], payload: UserInviteRequest) -> UserCompanyAccess:
    email = payload.email.strip().lower()
    mobile = payload.mobile_number.strip()
    by_email = database.scalar(select(User).where(User.email == email))
    by_mobile = database.scalar(select(User).where(User.mobile_number == mobile))
    if by_email and by_mobile and by_email.id != by_mobile.id:
        raise AdministrationError("The email and mobile number already belong to different identities.")
    user = by_email or by_mobile
    roles = selectable_roles(database, company.id, payload.role_ids, actor_codes)
    validate_defaults(database, company.id, payload.default_branch_id, payload.default_warehouse_id)
    if user is None:
        user = User(name=payload.name.strip(), email=email, mobile_number=mobile, account_state="invited", email_verified=False, mobile_verified=False)
        database.add(user)
        database.flush()
        activation_token = auth_service.issue_auth_token(database, user, "activation")
        development_notifications.deliver("activation", user.email, activation_token)
        action = "user_invited"
    elif user.account_state == "inactive" or not user.is_active:
        raise AdministrationError("This identity is inactive and must be managed by Pruvian Technologies.")
    else:
        if user.account_state == "invited":
            auth_service.request_activation(database, user.email or "")
        action = "company_access_granted"
    if access_for_company_user(database, company.id, user.id):
        raise AdministrationError("This user already has access to this company.")
    access = UserCompanyAccess(user=user, company=company, default_branch_id=payload.default_branch_id, default_warehouse_id=payload.default_warehouse_id)
    database.add(access)
    database.flush()
    for role in roles:
        database.add(RoleAssignment(user=user, role=role, company_id=company.id))
    audit(database, company.id, actor, action, user, "company-wide role assignment")
    return access


def update_user(database: Session, company: Company, actor: User, actor_codes: set[str], user_id: UUID, payload: UserUpdateRequest) -> UserCompanyAccess:
    access = access_for_company_user(database, company.id, user_id)
    if access is None:
        raise AdministrationError("The requested user is not available in this company.")
    if not access.is_active:
        raise AdministrationError("Activate this company user before initiating credentials.")
    if any(role.name == "Owner" and role.is_system_managed for role in assignments_for_user(database, company.id, user_id)):
        raise AdministrationForbidden("Primary Owner access is controlled by Pruvian Technologies.")
    roles = selectable_roles(database, company.id, payload.role_ids, actor_codes)
    validate_defaults(database, company.id, payload.default_branch_id, payload.default_warehouse_id)
    access.user.name = payload.name.strip()
    access.default_branch_id = payload.default_branch_id
    access.default_warehouse_id = payload.default_warehouse_id
    for assignment in list(database.scalars(select(RoleAssignment).where(RoleAssignment.user_id == user_id, RoleAssignment.company_id == company.id)).all()):
        database.delete(assignment)
    for role in roles:
        database.add(RoleAssignment(user=access.user, role=role, company_id=company.id))
    audit(database, company.id, actor, "user_updated", access.user, "company-wide role assignment")
    return access


def set_user_access_status(database: Session, company: Company, actor: User, user_id: UUID, is_active: bool) -> UserCompanyAccess:
    access = access_for_company_user(database, company.id, user_id)
    if access is None:
        raise AdministrationError("The requested user is not available in this company.")
    if any(role.name == "Owner" and role.is_system_managed for role in assignments_for_user(database, company.id, user_id)):
        raise AdministrationForbidden("Primary Owner access is controlled by Pruvian Technologies.")
    access.is_active = is_active
    if not is_active:
        revoke_user_sessions(database, access.user_id)
    audit(database, company.id, actor, "user_access_activated" if is_active else "user_access_deactivated", access.user)
    return access


def revoke_user_sessions(database: Session, user_id: UUID) -> None:
    for session in database.scalars(select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.is_platform_session.is_(False), AuthSession.revoked_at.is_(None))):
        session.revoked_at = auth_service.now()


def initiate_reset(database: Session, company: Company, actor: User, user_id: UUID) -> None:
    access = access_for_company_user(database, company.id, user_id)
    if access is None:
        raise AdministrationError("The requested user is not available in this company.")
    if not access.is_active:
        raise AdministrationError("Activate this company user before initiating credentials.")
    if access.user.account_state == "invited":
        auth_service.request_activation(database, access.user.email or "")
        action = "activation_resent"
    else:
        auth_service.request_password_reset(database, access.user.email or "")
        action = "password_reset_initiated"
    audit(database, company.id, actor, action, access.user)


def force_logout(database: Session, company: Company, actor: User, user_id: UUID) -> None:
    access = access_for_company_user(database, company.id, user_id)
    if access is None:
        raise AdministrationError("The requested user is not available in this company.")
    if any(role.name == "Owner" and role.is_system_managed for role in assignments_for_user(database, company.id, user_id)):
        raise AdministrationForbidden("Primary Owner access is controlled by Pruvian Technologies.")
    revoke_user_sessions(database, user_id)
    audit(database, company.id, actor, "force_logout", access.user)


def create_role(database: Session, company: Company, actor: User, actor_codes: set[str], payload: RoleInput) -> Role:
    requested = set(payload.permission_codes)
    if not requested.issubset(ALL_PERMISSIONS) or not requested.issubset(actor_codes):
        raise AdministrationForbidden("You cannot grant permissions you do not possess.")
    name = payload.name.strip()
    if name in STANDARD_ROLE_PERMISSIONS:
        raise AdministrationError("Standard role names are reserved.")
    if database.scalar(select(Role).where(Role.company_id == company.id, Role.name == name)):
        raise AdministrationError("A role with this name already exists in this company.")
    catalogue = {item.code: item for item in permissions(database)}
    role = Role(name=name, scope="company", company_id=company.id, description=(payload.description or "").strip() or None, is_active=payload.is_active, is_system_managed=False)
    role.permissions = [catalogue[code] for code in sorted(requested)]
    database.add(role)
    audit(database, company.id, actor, "custom_role_created", details=name)
    return role


def update_role(database: Session, company: Company, actor: User, actor_codes: set[str], role_id: UUID, payload: RoleInput) -> Role:
    role = database.scalar(select(Role).where(Role.id == role_id, Role.company_id == company.id))
    if role is None:
        raise AdministrationError("The requested role is not available in this company.")
    if role.is_system_managed:
        raise AdministrationForbidden("System-managed roles cannot be changed.")
    requested = set(payload.permission_codes)
    if not requested.issubset(ALL_PERMISSIONS) or not requested.issubset(actor_codes):
        raise AdministrationForbidden("You cannot grant permissions you do not possess.")
    name = payload.name.strip()
    conflict = database.scalar(select(Role).where(Role.company_id == company.id, Role.name == name, Role.id != role.id))
    if conflict:
        raise AdministrationError("A role with this name already exists in this company.")
    role.name, role.description, role.is_active = name, (payload.description or "").strip() or None, payload.is_active
    catalogue = {item.code: item for item in permissions(database)}
    role.permissions = [catalogue[code] for code in sorted(requested)]
    audit(database, company.id, actor, "custom_role_updated", details=name)
    return role


def clone_role(database: Session, company: Company, actor: User, actor_codes: set[str], source_id: UUID, name: str) -> Role:
    source = database.scalar(select(Role).where(Role.id == source_id, Role.company_id == company.id))
    if source is None:
        raise AdministrationError("The requested role is not available in this company.")
    return create_role(database, company, actor, actor_codes, RoleInput(name=name, description=source.description, permission_codes=[item.code for item in source.permissions], is_active=True))


def audit_events(database: Session, company_id: UUID) -> list[UserManagementAuditEvent]:
    return list(database.scalars(select(UserManagementAuditEvent).where(UserManagementAuditEvent.company_id == company_id).order_by(UserManagementAuditEvent.created_at.desc()).limit(50)).all())
