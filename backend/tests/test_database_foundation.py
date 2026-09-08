"""Automated checks for the P003 database foundation."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.company_context import CompanyContext, CompanyContextAccessError, require_active_company_access
from app.core.config import Settings
from app.db.base import Base
from app.models import Branch, Company, User, UserCompanyAccess, Warehouse


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")  # type: ignore[attr-defined]

    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session
    engine.dispose()


def make_user(email: str = "user@example.com", mobile_number: str = "+919876543210") -> User:
    return User(name="Test User", email=email, mobile_number=mobile_number)


def test_database_configuration_supports_explicit_database_url() -> None:
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://user:secret@db:5432/erp")

    assert settings.sqlalchemy_database_url == "postgresql+psycopg://user:secret@db:5432/erp"


def test_database_configuration_builds_postgresql_url_from_environment_fields() -> None:
    settings = Settings(
        _env_file=None,
        postgres_db="erp_test",
        postgres_user="erp_user",
        postgres_password="safe password",
        postgres_host="database",
        postgres_port=5433,
    )

    assert settings.sqlalchemy_database_url.startswith("postgresql+psycopg://erp_user:")
    assert settings.sqlalchemy_database_url.endswith("@database:5433/erp_test")


def test_user_can_access_multiple_companies_and_company_needs_no_branch_or_warehouse(
    session: Session,
) -> None:
    user = make_user()
    first_company = Company(business_name="First Company")
    second_company = Company(business_name="Second Company")
    session.add_all(
        [
            user,
            first_company,
            second_company,
            UserCompanyAccess(user=user, company=first_company),
            UserCompanyAccess(user=user, company=second_company),
        ]
    )
    session.commit()

    assert {access.company.business_name for access in user.company_accesses} == {
        "First Company",
        "Second Company",
    }
    assert first_company.branches == []
    assert first_company.warehouses == []


def test_branch_and_warehouse_belong_to_their_company(session: Session) -> None:
    company = Company(business_name="Company A")
    branch = Branch(company=company, name="Pune")
    warehouse = Warehouse(company=company, name="Main Warehouse")
    session.add_all([company, branch, warehouse])
    session.commit()

    assert branch.company_id == company.id
    assert warehouse.company_id == company.id
    assert company.branches == [branch]
    assert company.warehouses == [warehouse]


def test_unique_identity_and_company_access_constraints_are_enforced(session: Session) -> None:
    user = make_user()
    company = Company(business_name="Company A")
    session.add_all([user, company, UserCompanyAccess(user=user, company=company)])
    session.commit()

    session.add(UserCompanyAccess(user_id=user.id, company_id=company.id))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    session.add(make_user(email=user.email, mobile_number="+919876543211"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_company_context_requires_active_access(session: Session) -> None:
    user = make_user()
    company = Company(business_name="Company A")
    session.add_all([user, company, UserCompanyAccess(user=user, company=company)])
    session.commit()

    access = require_active_company_access(session, CompanyContext(user_id=user.id, company_id=company.id))
    assert access.company_id == company.id

    company.is_active = False
    session.commit()

    with pytest.raises(CompanyContextAccessError):
        require_active_company_access(session, CompanyContext(user_id=user.id, company_id=company.id))

    with pytest.raises(CompanyContextAccessError):
        require_active_company_access(session, CompanyContext(user_id=user.id, company_id=Company().id))


def test_initial_alembic_migration_creates_core_tables(tmp_path: Path) -> None:
    backend_directory = Path(__file__).resolve().parents[1]
    config = Config(str(backend_directory / "alembic.ini"))
    config.set_main_option("script_location", str(backend_directory / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{tmp_path / 'migration.db'}")

    command.upgrade(config, "head")
    engine = create_engine(config.get_main_option("sqlalchemy.url"))
    try:
        assert {"users", "companies", "user_company_accesses", "branches", "warehouses"}.issubset(
            inspect(engine).get_table_names()
        )
    finally:
        engine.dispose()
    command.downgrade(config, "base")