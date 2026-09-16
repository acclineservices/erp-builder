"""P007 company administration, RBAC, lifecycle, and tenant-isolation tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from uuid import UUID

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import AuthenticationMethod, Branch, Company, Role, RoleAssignment, Session as AuthSession, User, UserCompanyAccess, Warehouse
from app.services import administration as administration_service
from app.services import auth as auth_service


@pytest.fixture
def database() -> Session:
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(database: Session):
    def override_db():
        yield database
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def user(database: Session, email: str, mobile: str, name: str = "Company Admin") -> User:
    item = User(name=name, email=email, mobile_number=mobile, account_state="active", email_verified=True, mobile_verified=True)
    database.add(item); database.flush()
    database.add(AuthenticationMethod(user=item, method_type="email_password", credential_hash=hash_password("correct-password"), is_verified=True))
    database.add(AuthenticationMethod(user=item, method_type="mobile_otp", is_verified=True))
    database.commit()
    return item


def header(company: Company) -> dict[str, str]:
    return {"X-Company-ID": str(company.id)}


def provision_admin(database: Session, client: TestClient) -> tuple[User, Company, Company]:
    actor = user(database, "admin@example.com", "+919876543210")
    primary, foreign = Company(business_name="Primary"), Company(business_name="Foreign")
    database.add_all([primary, foreign]); database.flush()
    database.add(UserCompanyAccess(user=actor, company=primary)); administration_service.ensure_company_catalogue(database, primary)
    admin_role = database.scalar(select(Role).where(Role.company_id == primary.id, Role.name == "Admin"))
    assert admin_role is not None
    database.add(RoleAssignment(user=actor, role=admin_role, company_id=primary.id)); database.commit()
    assert client.post("/auth/login/email", json={"email": actor.email, "password": "correct-password"}).status_code == 200
    return actor, primary, foreign


def role_id(database: Session, company: Company, name: str = "Viewer") -> str:
    role = database.scalar(select(Role).where(Role.company_id == company.id, Role.name == name))
    assert role is not None
    return str(role.id)


def invite_payload(database: Session, company: Company, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": "New User", "email": "new@example.com", "mobile_number": "+919876543211", "role_ids": [role_id(database, company)]}
    payload.update(overrides)
    return payload


def test_company_user_list_invite_activation_and_duplicate_contact_protection(client: TestClient, database: Session) -> None:
    _, primary, _ = provision_admin(database, client)
    created = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary))
    assert created.status_code == 201
    assert created.json()["account_state"] == "invited"
    assert created.json()["email"] == "new@example.com"
    assert client.get("/administration/users", headers=header(primary)).status_code == 200
    duplicate_email = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary, mobile_number="+919876543212"))
    assert duplicate_email.status_code == 422
    duplicate_mobile = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary, email="other@example.com"))
    assert duplicate_mobile.status_code == 422


def test_company_isolation_default_locations_and_inactive_session_behavior(client: TestClient, database: Session) -> None:
    _, primary, foreign = provision_admin(database, client)
    local_branch, foreign_branch = Branch(company=primary, name="Local"), Branch(company=foreign, name="Foreign")
    local_warehouse = Warehouse(company=primary, name="Local warehouse", branch=local_branch)
    foreign_warehouse = Warehouse(company=foreign, name="Foreign warehouse", branch=foreign_branch)
    database.add_all([local_branch, foreign_branch, local_warehouse, foreign_warehouse]); database.commit()
    invalid = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary, default_branch_id=str(foreign_branch.id)))
    assert invalid.status_code == 422
    invalid = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary, default_warehouse_id=str(foreign_warehouse.id)))
    assert invalid.status_code == 422
    invalid = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary, default_branch_id=str(local_branch.id), default_warehouse_id=str(foreign_warehouse.id)))
    assert invalid.status_code == 422
    created = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary, default_branch_id=str(local_branch.id), default_warehouse_id=str(local_warehouse.id)))
    assert created.status_code == 201
    target = database.get(User, UUID(created.json()["id"])); assert target is not None
    target.account_state = "active"; target.email_verified = True; target.mobile_verified = True
    database.add(AuthenticationMethod(user=target, method_type="email_password", credential_hash=hash_password("correct-password"), is_verified=True)); database.commit()
    session, _ = auth_service.create_session(database, target, False); database.commit()
    disabled = client.patch(f"/administration/users/{target.id}/status", headers=header(primary), json={"is_active": False})
    assert disabled.status_code == 200 and disabled.json()["company_access_active"] is False
    database.refresh(session); assert session.revoked_at is not None
    assert client.get("/administration/users", headers=header(foreign)).status_code == 403


def test_multiple_roles_add_permissions_and_prevent_self_escalation_and_owner_mutation(client: TestClient, database: Session) -> None:
    actor, primary, _ = provision_admin(database, client)
    sales = role_id(database, primary, "Sales User"); viewer = role_id(database, primary, "Viewer")
    created = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary, role_ids=[sales, viewer]))
    assert created.status_code == 201 and set(created.json()["role_names"]) == {"Sales User", "Viewer"}
    custom = client.post("/administration/roles", headers=header(primary), json={"name": "Limited sales", "description": "Sales view", "permission_codes": ["sales.view"], "is_active": True})
    assert custom.status_code == 201
    role = database.get(Role, UUID(custom.json()["id"])); assert role is not None
    actor_role = database.scalar(select(Role).where(Role.company_id == primary.id, Role.name == "Admin")); assert actor_role is not None
    restricted = Role(name="Restricted admin", scope="company", company_id=primary.id)
    restricted.permissions = [permission for permission in actor_role.permissions if permission.code != "sales.approve"]
    database.add(restricted); database.flush()
    database.add(RoleAssignment(user=actor, role=restricted, company_id=primary.id))
    for assignment in database.scalars(select(RoleAssignment).where(RoleAssignment.user_id == actor.id, RoleAssignment.company_id == primary.id, RoleAssignment.role_id == actor_role.id)):
        database.delete(assignment)
    database.commit()
    escalation = client.post("/administration/roles", headers=header(primary), json={"name": "Escalation", "description": None, "permission_codes": ["sales.approve"], "is_active": True})
    assert escalation.status_code == 403
    owner = database.scalar(select(Role).where(Role.company_id == primary.id, Role.name == "Owner")); assert owner is not None
    assert client.put(f"/administration/roles/{owner.id}", headers=header(primary), json={"name": "Renamed", "description": None, "permission_codes": [], "is_active": False}).status_code == 403
    database.add(RoleAssignment(user=actor, role=owner, company_id=primary.id)); database.commit()
    assert client.patch(f"/administration/users/{actor.id}/status", headers=header(primary), json={"is_active": False}).status_code == 403


def test_custom_role_clone_force_logout_reset_and_audit_events(client: TestClient, database: Session) -> None:
    _, primary, _ = provision_admin(database, client)
    custom = client.post("/administration/roles", headers=header(primary), json={"name": "Audit role", "description": "Initial", "permission_codes": ["reports.view"], "is_active": True})
    assert custom.status_code == 201
    clone = client.post(f"/administration/roles/{custom.json()['id']}/clone", headers=header(primary), json={"name": "Audit role copy", "description": None, "permission_codes": [], "is_active": True})
    assert clone.status_code == 201 and clone.json()["is_system_managed"] is False
    created = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary, email="security@example.com", mobile_number="+919876543213"))
    target_id = created.json()["id"]
    assert client.post(f"/administration/users/{target_id}/reset", headers=header(primary)).status_code == 200
    assert client.post(f"/administration/users/{target_id}/force-logout", headers=header(primary)).status_code == 200
    state = client.get("/administration/bootstrap", headers=header(primary))
    assert state.status_code == 200
    actions = {event["action"] for event in state.json()["audit_events"]}
    assert {"custom_role_created", "user_invited", "activation_resent", "force_logout"}.issubset(actions)


def test_standard_role_seed_is_idempotent_and_cross_company_roles_are_rejected(client: TestClient, database: Session) -> None:
    _, primary, foreign = provision_admin(database, client)
    administration_service.ensure_company_catalogue(database, primary); administration_service.ensure_company_catalogue(database, primary); administration_service.ensure_company_catalogue(database, foreign); database.commit()
    assert len([item for item in administration_service.roles_for_company(database, primary.id) if item.is_system_managed]) == 8
    foreign_viewer = role_id(database, foreign)
    rejected = client.post("/administration/users", headers=header(primary), json=invite_payload(database, primary, role_ids=[foreign_viewer]))
    assert rejected.status_code == 422
