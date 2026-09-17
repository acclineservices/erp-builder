"""Company-scoped item and category master-data models."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Company, Warehouse


class ItemCategory(TimestampMixin, Base):
    __tablename__ = "item_categories"
    __table_args__ = (UniqueConstraint("company_id", "name", name="item_category_company_name"), Index("uq_item_category_code", "company_id", "code", unique=True, postgresql_where=text("code IS NOT NULL"), sqlite_where=text("code IS NOT NULL")))
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    company: Mapped[Company] = relationship(back_populates="item_categories")
    items: Mapped[list[Item]] = relationship(back_populates="category")


class Item(TimestampMixin, Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("item_type IN ('goods', 'service')", name="item_type"),
        CheckConstraint("purchase_price IS NULL OR purchase_price >= 0", name="item_purchase_price"),
        CheckConstraint("selling_price IS NULL OR selling_price >= 0", name="item_selling_price"),
        CheckConstraint("opening_stock >= 0", name="item_opening_stock"),
        CheckConstraint("reorder_level IS NULL OR reorder_level >= 0", name="item_reorder_level"),
        Index("uq_item_code", "company_id", "code", unique=True),
        Index("uq_item_barcode", "company_id", "barcode", unique=True, postgresql_where=text("barcode IS NOT NULL"), sqlite_where=text("barcode IS NOT NULL")),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[UUID | None] = mapped_column(ForeignKey("item_categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    default_warehouse_id: Mapped[UUID | None] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    item_type: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uom_code: Mapped[str] = mapped_column(String(16), nullable=False, default="PCS", server_default="PCS")
    hsn_sac_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(128), nullable=True)
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    selling_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    gst_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    track_inventory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    opening_stock: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=Decimal("0"), server_default="0")
    reorder_level: Mapped[Decimal | None] = mapped_column(Numeric(14, 3), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    company: Mapped[Company] = relationship(back_populates="items")
    category: Mapped[ItemCategory | None] = relationship(back_populates="items")
    default_warehouse: Mapped[Warehouse | None] = relationship()


class ItemCodeSequence(Base):
    __tablename__ = "item_code_sequences"
    __table_args__ = (UniqueConstraint("company_id", name="item_code_sequence_company"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
