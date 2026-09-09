"""P006 organization API tests, including tenant-isolation boundaries."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import AuthenticationMethod, Branch, Company, User, UserCompanyAccess, Warehouse


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


def make_authenticated_user(database: Session) -> User:
    user = User(
        name="Organization User",
        email="organization@example.com",
        mobile_number="+919876543210",
        account_state="active",
        email_verified=True,
        mobile_verified=True,
    )
    database.add(user)
    database.flush()
    database.add(AuthenticationMethod(
        user=user,
        method_type="email_password",
        credential_hash=hash_password("correct-password"),
        is_verified=True,
    ))
    database.commit()
    return user


def login(client: TestClient) -> None:
    response = client.post("/auth/login/email", json={"email": "organization@example.com", "password": "correct-password"})
    assert response.status_code == 200


def provision_companies(database: Session, user: User) -> tuple[Company, Company, Company]:
    primary = Company(business_name="Primary Manufacturing")
    secondary = Company(business_name="Secondary Trading")
    ungranted = Company(business_name="Unrelated Company")
    database.add_all([primary, secondary, ungranted])
    database.flush()
    database.add_all([UserCompanyAccess(user=user, company=primary), UserCompanyAccess(user=user, company=secondary)])
    database.commit()
    return primary, secondary, ungranted


def context(company: Company) -> dict[str, str]:
    return {"X-Company-ID": str(company.id)}


def test_authorized_company_access_update_and_ungranted_context(client: TestClient, database: Session) -> None:
    user = make_authenticated_user(database)
    primary, _, ungranted = provision_companies(database, user)
    login(client)

    response = client.get("/organization/company", headers=context(primary))
    assert response.status_code == 200
    assert response.json()["business_name"] == primary.business_name
    assert client.get("/organization/company", headers=context(ungranted)).status_code == 403

    response = client.put("/organization/company", headers=context(primary), json={
        "legal_name": "Primary Manufacturing LLP", "display_name": "Primary", "business_type": "proprietorship",
        "gst_status": "registered", "gstin": "27ABCDE1234F1Z5", "email": "accounts@example.com",
        "phone": "+912212345678", "address_line1": "Industrial Estate", "city": "Mumbai", "country": "India",
    })
    assert response.status_code == 200
    assert response.json()["legal_name"] == "Primary Manufacturing LLP"
    assert response.json()["setup_progress"] == 100


def test_optional_zero_branch_and_branch_lifecycle_with_isolation(client: TestClient, database: Session) -> None:
    user = make_authenticated_user(database)
    primary, secondary, _ = provision_companies(database, user)
    foreign_branch = Branch(company=secondary, name="Foreign branch")
    database.add(foreign_branch)
    database.commit()
    login(client)

    assert client.get("/organization/branches", headers=context(primary)).json() == []
    created = client.post("/organization/branches", headers=context(primary), json={
        "name": "Pune Office", "code": "PNQ", "address_line1": "Market Road", "city": "Pune", "phone": "+912012345678",
    })
    assert created.status_code == 201
    branch_id = created.json()["id"]
    updated = client.put(f"/organization/branches/{branch_id}", headers=context(primary), json={"name": "Pune Operations", "code": "PNQ"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Pune Operations"
    deactivated = client.patch(f"/organization/branches/{branch_id}/status", headers=context(primary), json={"is_active": False})
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False
    assert client.get(f"/organization/branches/{foreign_branch.id}", headers=context(primary)).status_code == 404


def test_optional_zero_warehouse_and_warehouse_lifecycle_with_same_company_branch_validation(client: TestClient, database: Session) -> None:
    user = make_authenticated_user(database)
    primary, secondary, _ = provision_companies(database, user)
    primary_branch = Branch(company=primary, name="Primary branch")
    foreign_branch = Branch(company=secondary, name="Foreign branch")
    foreign_warehouse = Warehouse(company=secondary, name="Foreign warehouse")
    database.add_all([primary_branch, foreign_branch, foreign_warehouse])
    database.commit()
    login(client)

    assert client.get("/organization/warehouses", headers=context(primary)).json() == []
    invalid = client.post("/organization/warehouses", headers=context(primary), json={"name": "Invalid", "branch_id": str(foreign_branch.id)})
    assert invalid.status_code == 422
    created = client.post("/organization/warehouses", headers=context(primary), json={
        "name": "Main Store", "code": "MAIN", "branch_id": str(primary_branch.id), "contact_person": "Store Manager",
        "contact_number": "+919000000000", "address_line1": "Industrial Estate", "city": "Pune",
    })
    assert created.status_code == 201
    warehouse_id = created.json()["id"]
    updated = client.put(f"/organization/warehouses/{warehouse_id}", headers=context(primary), json={
        "name": "Main Store Updated", "code": "MAIN", "branch_id": None,
    })
    assert updated.status_code == 200
    assert updated.json()["branch_id"] is None
    deactivated = client.patch(f"/organization/warehouses/{warehouse_id}/status", headers=context(primary), json={"is_active": False})
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False
    assert client.get(f"/organization/warehouses/{foreign_warehouse.id}", headers=context(primary)).status_code == 404
