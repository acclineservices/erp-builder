"""Safety and idempotency coverage for the operator-only staging bootstrap CLI."""

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.base import Base
from app.models import AuthenticationMethod, Company, Role, RoleAssignment, User, UserCompanyAccess
from app.scripts.bootstrap_staging import (
    BootstrapConfiguration,
    StagingBootstrapError,
    bootstrap_staging,
    configuration_from_environment,
)


@pytest.fixture
def database() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def bootstrap_configuration() -> BootstrapConfiguration:
    return BootstrapConfiguration(
        email="staging-owner@example.com",
        mobile="+919876543210",
        password="safe-bootstrap-password",
        company_name="Pruvian Staging Company",
    )


def test_bootstrap_refuses_non_staging_environment() -> None:
    with pytest.raises(StagingBootstrapError, match="APP_ENV=staging"):
        configuration_from_environment(
            {
                "APP_ENV": "development",
                "STAGING_BOOTSTRAP_EMAIL": "owner@example.com",
                "STAGING_BOOTSTRAP_MOBILE": "+919876543210",
                "STAGING_BOOTSTRAP_PASSWORD": "safe-password",
                "STAGING_BOOTSTRAP_COMPANY_NAME": "Staging Company",
            }
        )


def test_bootstrap_creates_verified_owner_company_access_and_standard_owner_role(database: Session) -> None:
    configuration = bootstrap_configuration()
    result = bootstrap_staging(database, configuration)
    database.commit()

    user = database.scalar(select(User).where(User.email == configuration.email))
    company = database.scalar(select(Company).where(Company.business_name == configuration.company_name))
    assert result.company_created is True
    assert result.owner_created is True
    assert result.owner_role_assigned is True
    assert user is not None and company is not None
    assert user.is_active is True
    assert user.is_platform_admin is False
    assert user.account_state == "active"
    assert user.email_verified is True and user.mobile_verified is True
    password_method = database.scalar(
        select(AuthenticationMethod).where(AuthenticationMethod.user_id == user.id, AuthenticationMethod.method_type == "email_password")
    )
    assert password_method is not None and password_method.credential_hash != configuration.password
    assert verify_password(configuration.password, password_method.credential_hash or "")
    assert database.scalar(
        select(UserCompanyAccess).where(
            UserCompanyAccess.user_id == user.id,
            UserCompanyAccess.company_id == company.id,
            UserCompanyAccess.is_active.is_(True),
        )
    ) is not None
    owner_role = database.scalar(select(Role).where(Role.company_id == company.id, Role.name == "Owner"))
    assert owner_role is not None and owner_role.is_system_managed is True and owner_role.is_active is True
    assert database.scalar(
        select(RoleAssignment).where(
            RoleAssignment.user_id == user.id,
            RoleAssignment.role_id == owner_role.id,
            RoleAssignment.company_id == company.id,
        )
    ) is not None


def test_bootstrap_repeat_is_idempotent(database: Session) -> None:
    configuration = bootstrap_configuration()
    bootstrap_staging(database, configuration)
    database.commit()
    first_hash = database.scalar(select(AuthenticationMethod.credential_hash).where(AuthenticationMethod.method_type == "email_password"))

    second = bootstrap_staging(database, configuration)
    database.commit()

    assert second.company_created is False
    assert second.owner_created is False
    assert second.owner_role_assigned is False
    assert database.scalar(select(func.count()).select_from(User)) == 1
    assert database.scalar(select(func.count()).select_from(Company)) == 1
    assert database.scalar(select(func.count()).select_from(UserCompanyAccess)) == 1
    assert database.scalar(select(func.count()).select_from(RoleAssignment)) == 1
    assert database.scalar(select(AuthenticationMethod.credential_hash).where(AuthenticationMethod.method_type == "email_password")) == first_hash
