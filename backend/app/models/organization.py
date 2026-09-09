"""Company, branch, warehouse, and user-company access data models."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.identity import User


class Company(TimestampMixin, Base):
    """A customer business and fundamental data-isolation boundary."""

    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_type: Mapped[str] = mapped_column(String(64), nullable=False, default="proprietorship", server_default="proprietorship")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", server_default="active")
    gst_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    user_accesses: Mapped[list[UserCompanyAccess]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    branches: Mapped[list[Branch]] = relationship(back_populates="company", cascade="all, delete-orphan")
    warehouses: Mapped[list[Warehouse]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class UserCompanyAccess(TimestampMixin, Base):
    """Explicit access for a user operating in a company context."""

    __tablename__ = "user_company_accesses"
    __table_args__ = (UniqueConstraint("user_id", "company_id", name="user_company_access"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    user: Mapped[User] = relationship(back_populates="company_accesses")
    company: Mapped[Company] = relationship(back_populates="user_accesses")


class Branch(TimestampMixin, Base):
    """An optional company branch."""

    __tablename__ = "branches"
    __table_args__ = (UniqueConstraint("company_id", "name", name="branch_company_name"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    company: Mapped[Company] = relationship(back_populates="branches")
    warehouses: Mapped[list[Warehouse]] = relationship(back_populates="branch")


class Warehouse(TimestampMixin, Base):
    """An optional company warehouse, independent of branch adoption."""

    __tablename__ = "warehouses"
    __table_args__ = (UniqueConstraint("company_id", "name", name="warehouse_company_name"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    branch_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    company: Mapped[Company] = relationship(back_populates="warehouses")
    branch: Mapped[Branch | None] = relationship(back_populates="warehouses")
