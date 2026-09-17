"""P008 customer/supplier tenant, permission, and validation coverage."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import AuthenticationMethod, Company, Party, Role, RoleAssignment, User, UserCompanyAccess, UserManagementAuditEvent
from app.services import administration as administration_service


@pytest.fixture
def database() -> Session:
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session: yield session
    engine.dispose()


@pytest.fixture
def client(database: Session):
    def override_db(): yield database
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client: yield test_client
    app.dependency_overrides.clear()


def provision(database: Session, client: TestClient) -> tuple[Company, Company]:
    user = User(name="Party Admin", email="party@example.com", mobile_number="+919876543210", account_state="active", email_verified=True, mobile_verified=True)
    primary, foreign = Company(business_name="Primary"), Company(business_name="Foreign")
    database.add_all([user, primary, foreign]); database.flush()
    database.add(AuthenticationMethod(user=user, method_type="email_password", credential_hash=hash_password("correct-password"), is_verified=True))
    database.add_all([UserCompanyAccess(user=user, company=primary), UserCompanyAccess(user=user, company=foreign)])
    administration_service.ensure_company_catalogue(database, primary); administration_service.ensure_company_catalogue(database, foreign)
    primary_admin = database.scalar(select(Role).where(Role.company_id == primary.id, Role.name == "Admin")); assert primary_admin
    foreign_admin = database.scalar(select(Role).where(Role.company_id == foreign.id, Role.name == "Admin")); assert foreign_admin
    database.add_all([
        RoleAssignment(user=user, role=primary_admin, company_id=primary.id),
        RoleAssignment(user=user, role=foreign_admin, company_id=foreign.id),
    ]); database.commit()
    assert client.post("/auth/login/email", json={"email": user.email, "password": "correct-password"}).status_code == 200
    return primary, foreign


def header(company: Company) -> dict[str, str]: return {"X-Company-ID": str(company.id)}
def customer(name: str = "Acme Customer", **values: object) -> dict[str, object]:
    return {"display_name": name, "gst_status": "unregistered", "mobile_number": "+919000000001", **values}


def test_customer_supplier_both_codes_and_audit(client: TestClient, database: Session) -> None:
    primary, _ = provision(database, client)
    created = client.post("/parties/customers", headers=header(primary), json=customer(party_type="both", contact_person="Asha", city="Mumbai", country="India", gst_status="registered", gstin="27ABCDE1234F1Z5", pan="ABCDE1234F"))
    assert created.status_code == 201
    body = created.json(); assert body["customer_code"] == "CUS-0001" and body["supplier_code"] == "SUP-0001" and body["party_type"] == "both" and body["contact_person"] == "Asha" and body["city"] == "Mumbai" and body["country"] == "India"
    assert client.get("/parties/suppliers", headers=header(primary)).json()[0]["id"] == body["id"]
    actions = {item.action for item in database.scalars(select(UserManagementAuditEvent)).all()}; assert "customer_created" in actions


def test_company_scoped_uniqueness_tax_validation_search_and_status(client: TestClient, database: Session) -> None:
    primary, foreign = provision(database, client)
    first = client.post("/parties/customers", headers=header(primary), json=customer(code="ACM-01", gst_status="registered", gstin="27ABCDE1234F1Z5", email="same@example.com")); assert first.status_code == 201
    assert client.post("/parties/customers", headers=header(primary), json=customer("Duplicate", code="ACM-01")).status_code == 409
    assert client.post("/parties/customers", headers=header(primary), json=customer("Duplicate GST", gst_status="registered", gstin="27ABCDE1234F1Z5")).status_code == 409
    assert client.post("/parties/customers", headers=header(foreign), json=customer("Foreign permitted", code="ACM-01", gst_status="registered", gstin="27ABCDE1234F1Z5")).status_code == 201
    assert len(client.get("/parties/customers?search=ACM-01", headers=header(primary)).json()) == 1
    assert client.patch(f"/parties/customers/{first.json()['id']}/status", headers=header(primary), json={"is_active": False}).json()["is_active"] is False
    assert len(client.get("/parties/customers?active=false", headers=header(primary)).json()) == 1
    assert client.post("/parties/suppliers", headers=header(primary), json=customer("Bad PAN", pan="INVALID")).status_code == 422
    assert client.post("/parties/suppliers", headers=header(primary), json=customer("Missing GST", gst_status="registered")).status_code == 422


def test_update_cross_company_id_and_permission_rejection(client: TestClient, database: Session) -> None:
    primary, foreign = provision(database, client)
    created = client.post("/parties/suppliers", headers=header(primary), json=customer("Vendor One")); assert created.status_code == 201
    party_id = created.json()["id"]
    updated = client.put(f"/parties/suppliers/{party_id}", headers=header(primary), json=customer("Vendor Updated", party_type="both")); assert updated.status_code == 200 and updated.json()["customer_code"] == "CUS-0001"
    assert client.get(f"/parties/suppliers/{party_id}", headers=header(foreign)).status_code == 404
    actor = database.scalar(select(User).where(User.email == "party@example.com")); assert actor
    for assignment in database.scalars(select(RoleAssignment).where(RoleAssignment.user_id == actor.id, RoleAssignment.company_id == primary.id)): database.delete(assignment)
    database.commit()
    assert client.get("/parties/customers", headers=header(primary)).status_code == 403
