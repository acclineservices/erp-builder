"""Safely provision the first Pruvian staging company owner.

This module deliberately has no HTTP route. It is an operator-only command:
``python -m app.scripts.bootstrap_staging``.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.session import SessionLocal
from app.models import AuthenticationMethod, Company, Role, RoleAssignment, User, UserCompanyAccess
from app.services.administration import ensure_company_catalogue


REQUIRED_ENVIRONMENT_VARIABLES = (
    "STAGING_BOOTSTRAP_EMAIL",
    "STAGING_BOOTSTRAP_MOBILE",
    "STAGING_BOOTSTRAP_PASSWORD",
    "STAGING_BOOTSTRAP_COMPANY_NAME",
)


class StagingBootstrapError(ValueError):
    """A safe, operator-actionable bootstrap configuration error."""


@dataclass(frozen=True)
class BootstrapConfiguration:
    email: str
    mobile: str
    password: str
    company_name: str


@dataclass(frozen=True)
class BootstrapResult:
    company_created: bool
    owner_created: bool
    owner_role_assigned: bool


def configuration_from_environment(environment: Mapping[str, str] | None = None) -> BootstrapConfiguration:
    """Read and validate the bootstrap inputs without exposing their values."""
    values = os.environ if environment is None else environment
    if values.get("APP_ENV", "").strip().lower() != "staging":
        raise StagingBootstrapError("This command may run only when APP_ENV=staging.")

    missing = [name for name in REQUIRED_ENVIRONMENT_VARIABLES if not values.get(name, "").strip()]
    if missing:
        raise StagingBootstrapError("Required staging bootstrap environment variables are missing.")

    email = values["STAGING_BOOTSTRAP_EMAIL"].strip().lower()
    mobile = values["STAGING_BOOTSTRAP_MOBILE"].strip()
    password = values["STAGING_BOOTSTRAP_PASSWORD"]
    company_name = values["STAGING_BOOTSTRAP_COMPANY_NAME"].strip()
    if not 3 <= len(email) <= 320 or not 6 <= len(mobile) <= 20 or not 8 <= len(password) <= 256 or len(company_name) > 255:
        raise StagingBootstrapError("Staging bootstrap environment variables have invalid lengths.")
    return BootstrapConfiguration(email=email, mobile=mobile, password=password, company_name=company_name)


def _matching_user(database: Session, configuration: BootstrapConfiguration) -> tuple[User | None, bool]:
    """Find one unambiguous identity, never merging unrelated users."""
    email_user = database.scalar(select(User).where(User.email == configuration.email))
    mobile_user = database.scalar(select(User).where(User.mobile_number == configuration.mobile))
    if email_user and mobile_user and email_user.id != mobile_user.id:
        raise StagingBootstrapError("Bootstrap identity conflicts with existing staging identities.")
    return email_user or mobile_user, email_user is None and mobile_user is None


def _ensure_authentication_methods(database: Session, user: User, configuration: BootstrapConfiguration) -> None:
    methods = {
        method.method_type: method
        for method in database.scalars(select(AuthenticationMethod).where(AuthenticationMethod.user_id == user.id)).all()
    }
    email_password = methods.get("email_password")
    if email_password is None:
        email_password = AuthenticationMethod(
            user=user,
            method_type="email_password",
            credential_hash=hash_password(configuration.password),
            is_verified=True,
            is_active=True,
        )
        database.add(email_password)
    else:
        if not email_password.credential_hash or not verify_password(configuration.password, email_password.credential_hash):
            email_password.credential_hash = hash_password(configuration.password)
        email_password.is_verified = True
        email_password.is_active = True

    mobile_otp = methods.get("mobile_otp")
    if mobile_otp is None:
        database.add(AuthenticationMethod(user=user, method_type="mobile_otp", is_verified=True, is_active=True))
    else:
        mobile_otp.is_verified = True
        mobile_otp.is_active = True


def bootstrap_staging(database: Session, configuration: BootstrapConfiguration) -> BootstrapResult:
    """Provision the staging owner, company, access, and Owner role idempotently."""
    user, owner_created = _matching_user(database, configuration)
    if user is None:
        user = User(
            name="Staging Owner",
            email=configuration.email,
            mobile_number=configuration.mobile,
            account_state="active",
            email_verified=True,
            mobile_verified=True,
            is_active=True,
            is_platform_admin=False,
        )
        database.add(user)
        database.flush()
    else:
        if user.email != configuration.email or user.mobile_number != configuration.mobile:
            raise StagingBootstrapError("Bootstrap identity does not match the existing staging identity.")
        user.is_active = True
        user.account_state = "active"
        user.email_verified = True
        user.mobile_verified = True

    _ensure_authentication_methods(database, user, configuration)

    companies = list(database.scalars(select(Company).where(Company.business_name == configuration.company_name)).all())
    if len(companies) > 1:
        raise StagingBootstrapError("Bootstrap company name matches multiple existing staging companies.")
    company_created = not companies
    company = companies[0] if companies else Company(business_name=configuration.company_name, status="active", is_active=True)
    if company_created:
        database.add(company)
        database.flush()
    else:
        company.status = "active"
        company.is_active = True

    access = database.scalar(
        select(UserCompanyAccess).where(UserCompanyAccess.user_id == user.id, UserCompanyAccess.company_id == company.id)
    )
    if access is None:
        database.add(UserCompanyAccess(user=user, company=company, is_active=True))
    else:
        access.is_active = True

    ensure_company_catalogue(database, company)
    owner_role = database.scalar(
        select(Role).where(Role.company_id == company.id, Role.name == "Owner", Role.is_system_managed.is_(True))
    )
    if owner_role is None:
        raise StagingBootstrapError("The standard Owner role could not be prepared.")
    owner_role.is_active = True
    assignment = database.scalar(
        select(RoleAssignment).where(
            RoleAssignment.user_id == user.id,
            RoleAssignment.role_id == owner_role.id,
            RoleAssignment.company_id == company.id,
        )
    )
    owner_role_assigned = assignment is None
    if assignment is None:
        database.add(RoleAssignment(user=user, role=owner_role, company_id=company.id))
    return BootstrapResult(
        company_created=company_created,
        owner_created=owner_created,
        owner_role_assigned=owner_role_assigned,
    )


def main() -> int:
    """Run the one-time command and print only safe operational state."""
    try:
        configuration = configuration_from_environment()
        with SessionLocal() as database:
            result = bootstrap_staging(database, configuration)
            database.commit()
    except StagingBootstrapError as error:
        print(f"Staging bootstrap refused: {error}")
        return 1
    except Exception:
        print("Staging bootstrap failed without completing changes.")
        return 1

    print(f"Staging company {'created' if result.company_created else 'existing'}.")
    print(f"Staging owner {'created' if result.owner_created else 'existing'}.")
    print(f"Owner role {'assigned' if result.owner_role_assigned else 'already assigned'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
