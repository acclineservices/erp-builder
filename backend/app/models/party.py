"""Company-scoped business-party master data for customers and suppliers."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Company


class Party(TimestampMixin, Base):
    """One legal/business entity that may be a customer, supplier, or both."""

    __tablename__ = "parties"
    __table_args__ = (
        CheckConstraint("party_type IN ('customer', 'supplier', 'both')", name="party_type"),
        CheckConstraint("customer_code IS NOT NULL OR supplier_code IS NOT NULL", name="party_has_role"),
        CheckConstraint("gst_status IN ('registered', 'unregistered', 'composition', 'exempt')", name="party_gst_status"),
        CheckConstraint("opening_balance >= 0", name="party_opening_balance"),
        CheckConstraint("opening_balance_type IN ('debit', 'credit')", name="party_opening_balance_type"),
        CheckConstraint("credit_limit IS NULL OR credit_limit >= 0", name="party_credit_limit"),
        CheckConstraint("payment_terms_days IS NULL OR payment_terms_days >= 0", name="party_payment_terms"),
        Index("uq_party_customer_code", "company_id", "customer_code", unique=True, postgresql_where=text("customer_code IS NOT NULL"), sqlite_where=text("customer_code IS NOT NULL")),
        Index("uq_party_supplier_code", "company_id", "supplier_code", unique=True, postgresql_where=text("supplier_code IS NOT NULL"), sqlite_where=text("supplier_code IS NOT NULL")),
        Index("uq_party_gstin", "company_id", "gstin", unique=True, postgresql_where=text("gstin IS NOT NULL"), sqlite_where=text("gstin IS NOT NULL")),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    party_type: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    supplier_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gst_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unregistered", server_default="unregistered")
    gstin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(16), nullable=True)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0")
    opening_balance_type: Mapped[str] = mapped_column(String(8), nullable=False, default="debit", server_default="debit")
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    payment_terms_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    company: Mapped[Company] = relationship(back_populates="parties")
    contacts: Mapped[list[PartyContact]] = relationship(back_populates="party", cascade="all, delete-orphan")
    addresses: Mapped[list[PartyAddress]] = relationship(back_populates="party", cascade="all, delete-orphan")


class PartyContact(TimestampMixin, Base):
    """Small extensible contact foundation; P008 manages one primary contact."""

    __tablename__ = "party_contacts"
    __table_args__ = (UniqueConstraint("party_id", "contact_type", name="party_contact_type"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_type: Mapped[str] = mapped_column(String(32), nullable=False, default="primary", server_default="primary")
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mobile_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    alternate_mobile: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    party: Mapped[Party] = relationship(back_populates="contacts")


class PartyAddress(TimestampMixin, Base):
    """Address foundation supporting primary, billing, shipping, and registered uses."""

    __tablename__ = "party_addresses"
    __table_args__ = (UniqueConstraint("party_id", "address_type", name="party_address_type"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), nullable=False, index=True)
    address_type: Mapped[str] = mapped_column(String(32), nullable=False, default="primary", server_default="primary")
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    party: Mapped[Party] = relationship(back_populates="addresses")


class PartyCodeSequence(Base):
    """Company-local locked counters for deterministic customer/supplier codes."""

    __tablename__ = "party_code_sequences"
    __table_args__ = (UniqueConstraint("company_id", "sequence_type", name="party_code_sequence_company_type"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_type: Mapped[str] = mapped_column(String(16), nullable=False)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
