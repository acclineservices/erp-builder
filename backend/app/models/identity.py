"""Identity, authentication-method, and access-control data models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Table, Text, UniqueConstraint, text
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
        CheckConstraint(
            "account_state IN ('invited', 'active', 'inactive')", name="user_account_state"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    mobile_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_platform_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    account_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="invited", server_default="invited"
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    mobile_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    authentication_methods: Mapped[list[AuthenticationMethod]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    company_accesses: Mapped[list[UserCompanyAccess]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    role_assignments: Mapped[list[RoleAssignment]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list[Session]] = relationship(back_populates="user", cascade="all, delete-orphan")
    auth_tokens: Mapped[list[AuthToken]] = relationship(back_populates="user", cascade="all, delete-orphan")
    otp_challenges: Mapped[list[OtpChallenge]] = relationship(back_populates="user", cascade="all, delete-orphan")
    security_events: Mapped[list[SecurityEvent]] = relationship(back_populates="user", cascade="all, delete-orphan")


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


class Session(TimestampMixin, Base):
    """A revocable opaque browser session; only its digest is persisted."""

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remember_me: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_platform_session: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    user: Mapped[User] = relationship(back_populates="sessions")


class AuthToken(TimestampMixin, Base):
    """Single-use, hashed tokens for activation, email verification, and password reset."""

    __tablename__ = "auth_tokens"
    __table_args__ = (CheckConstraint("purpose IN ('activation', 'email_verification', 'password_reset')", name="auth_token_purpose"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="auth_tokens")


class OtpChallenge(TimestampMixin, Base):
    """Short-lived, attempt-limited mobile OTP challenge with a bcrypt digest."""

    __tablename__ = "otp_challenges"
    __table_args__ = (CheckConstraint("purpose IN ('mobile_login', 'mobile_verification', 'mobile_password_reset')", name="otp_challenge_purpose"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    mobile_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User | None] = relationship(back_populates="otp_challenges")


class SecurityEvent(TimestampMixin, Base):
    """Minimal audit record that intentionally contains no credential or token values."""

    __tablename__ = "security_events"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    user: Mapped[User | None] = relationship(back_populates="security_events")
