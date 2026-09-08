"""Identity, authentication-method, and access-control data models."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, String, Table, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import UserCompanyAccess


class User(TimestampMixin, Base):
    """A person who can access one or more ERP Builder companies."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email IS NOT NULL OR mobile_number IS NOT NULL", name="user_contact_present"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    mobile_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_platform_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    authentication_methods: Mapped[list[AuthenticationMethod]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    company_accesses: Mapped[list[UserCompanyAccess]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    role_assignments: Mapped[list[RoleAssignment]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AuthenticationMethod(TimestampMixin, Base):
    """An enabled login method mapped to a user without storing plaintext secrets."""

    __tablename__ = "authentication_methods"
    __table_args__ = (
        CheckConstraint(
            "method_type IN ('email_password', 'mobile_otp')", name="authentication_method_type"
        ),
        UniqueConstraint("user_id", "method_type", name="authentication_method_per_user"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    method_type: Mapped[str] = mapped_column(String(32), nullable=False)
    credential_hash: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    user: Mapped[User] = relationship(back_populates="authentication_methods")


class Role(TimestampMixin, Base):
    """A named RBAC role whose scope is platform-wide or company-specific."""

    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint("scope IN ('platform', 'company')", name="role_scope"),
        UniqueConstraint("scope", "name", name="role_scope_name"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    permissions: Mapped[list[Permission]] = relationship(
        secondary="role_permissions", back_populates="roles"
    )
    assignments: Mapped[list[RoleAssignment]] = relationship(back_populates="role")


class Permission(TimestampMixin, Base):
    """A permission definition which roles may be granted in future modules."""

    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    roles: Mapped[list[Role]] = relationship(secondary="role_permissions", back_populates="permissions")


class RoleAssignment(TimestampMixin, Base):
    """Assign a role to a user globally or in one company context."""

    __tablename__ = "role_assignments"
    __table_args__ = (
        Index(
            "uq_role_assignment_platform",
            "user_id",
            "role_id",
            unique=True,
            postgresql_where=text("company_id IS NULL"),
            sqlite_where=text("company_id IS NULL"),
        ),
        Index(
            "uq_role_assignment_company",
            "user_id",
            "role_id",
            "company_id",
            unique=True,
            postgresql_where=text("company_id IS NOT NULL"),
            sqlite_where=text("company_id IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    company_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )

    user: Mapped[User] = relationship(back_populates="role_assignments")
    role: Mapped[Role] = relationship(back_populates="assignments")


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        Uuid(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
