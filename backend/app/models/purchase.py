"""Company-scoped purchase document foundations; no stock or accounting posting."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Branch, Company, Warehouse
    from app.models.party import Party
    from app.models.item import Item


class PurchaseDocumentSequence(Base):
    __tablename__ = "purchase_document_sequences"
    __table_args__ = (UniqueConstraint("company_id", "document_type", name="purchase_document_sequence_company_type"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(16), nullable=False)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (CheckConstraint("status IN ('draft','submitted','approved','partially_received','received','cancelled')", name="purchase_order_status"), Index("uq_purchase_order_number", "company_id", "number", unique=True))
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), nullable=False, index=True)
    branch_id: Mapped[UUID | None] = mapped_column(ForeignKey("branches.id", ondelete="RESTRICT"), nullable=True, index=True)
    warehouse_id: Mapped[UUID | None] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=True, index=True)
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    order_date: Mapped[date] = mapped_column(nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(nullable=True)
    supplier_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft", index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0")
    discount_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0")
    tax_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0")
    round_off: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0")
    grand_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0")
    company: Mapped[Company] = relationship(back_populates="purchase_orders")
    supplier: Mapped[Party] = relationship()
    branch: Mapped[Branch | None] = relationship()
    warehouse: Mapped[Warehouse | None] = relationship()
    lines: Mapped[list[PurchaseOrderLine]] = relationship(back_populates="order", cascade="all, delete-orphan")


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    __table_args__ = (CheckConstraint("quantity > 0", name="purchase_order_line_quantity"), CheckConstraint("unit_rate >= 0", name="purchase_order_line_rate"), CheckConstraint("discount_percent >= 0 AND discount_percent <= 100", name="purchase_order_line_discount"))
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_id: Mapped[UUID] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("items.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uom_code: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_rate: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"), server_default="0")
    gst_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    order: Mapped[PurchaseOrder] = relationship(back_populates="lines")
    item: Mapped[Item] = relationship()


class GoodsReceipt(TimestampMixin, Base):
    __tablename__ = "goods_receipts"
    __table_args__ = (CheckConstraint("status IN ('draft','received','cancelled')", name="goods_receipt_status"), Index("uq_goods_receipt_number", "company_id", "number", unique=True))
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_order_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=True, index=True)
    warehouse_id: Mapped[UUID | None] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=True, index=True)
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    receipt_date: Mapped[date] = mapped_column(nullable=False)
    supplier_challan_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="received", server_default="received", index=True)
    company: Mapped[Company] = relationship(back_populates="goods_receipts")
    supplier: Mapped[Party] = relationship(); purchase_order: Mapped[PurchaseOrder | None] = relationship(); warehouse: Mapped[Warehouse | None] = relationship()
    lines: Mapped[list[GoodsReceiptLine]] = relationship(back_populates="receipt", cascade="all, delete-orphan")


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"
    __table_args__ = (CheckConstraint("received_quantity > 0", name="goods_receipt_line_received"), CheckConstraint("accepted_quantity >= 0", name="goods_receipt_line_accepted"), CheckConstraint("rejected_quantity >= 0", name="goods_receipt_line_rejected"))
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    goods_receipt_id: Mapped[UUID] = mapped_column(ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_order_line_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_order_lines.id", ondelete="RESTRICT"), nullable=True, index=True)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("items.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False); item_code: Mapped[str] = mapped_column(String(64), nullable=False); uom_code: Mapped[str] = mapped_column(String(16), nullable=False)
    ordered_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 3), nullable=True)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    accepted_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    rejected_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=Decimal("0"), server_default="0")
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt: Mapped[GoodsReceipt] = relationship(back_populates="lines"); item: Mapped[Item] = relationship(); purchase_order_line: Mapped[PurchaseOrderLine | None] = relationship()


class PurchaseInvoice(TimestampMixin, Base):
    __tablename__ = "purchase_invoices"
    __table_args__ = (CheckConstraint("status IN ('draft','approved','cancelled')", name="purchase_invoice_status"), Index("uq_purchase_invoice_number", "company_id", "number", unique=True), Index("uq_supplier_invoice_reference", "company_id", "supplier_id", "supplier_invoice_number", unique=True))
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_order_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=True, index=True)
    goods_receipt_id: Mapped[UUID | None] = mapped_column(ForeignKey("goods_receipts.id", ondelete="RESTRICT"), nullable=True, index=True)
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    supplier_invoice_number: Mapped[str] = mapped_column(String(128), nullable=False)
    supplier_invoice_date: Mapped[date] = mapped_column(nullable=False)
    document_date: Mapped[date] = mapped_column(nullable=False)
    due_date: Mapped[date | None] = mapped_column(nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String(255), nullable=True); notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft", server_default="draft", index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0"); discount_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0"); tax_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0"); round_off: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0"); grand_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"), server_default="0")
    company: Mapped[Company] = relationship(back_populates="purchase_invoices"); supplier: Mapped[Party] = relationship(); purchase_order: Mapped[PurchaseOrder | None] = relationship(); goods_receipt: Mapped[GoodsReceipt | None] = relationship()
    lines: Mapped[list[PurchaseInvoiceLine]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class PurchaseInvoiceLine(Base):
    __tablename__ = "purchase_invoice_lines"
    __table_args__ = (CheckConstraint("quantity > 0", name="purchase_invoice_line_quantity"), CheckConstraint("unit_rate >= 0", name="purchase_invoice_line_rate"), CheckConstraint("discount_percent >= 0 AND discount_percent <= 100", name="purchase_invoice_line_discount"))
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    purchase_invoice_id: Mapped[UUID] = mapped_column(ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False, index=True); item_id: Mapped[UUID] = mapped_column(ForeignKey("items.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False); item_code: Mapped[str] = mapped_column(String(64), nullable=False); description: Mapped[str | None] = mapped_column(Text, nullable=True); uom_code: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False); unit_rate: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False); discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"), server_default="0"); gst_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True); base_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False); discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False); tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False); line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    invoice: Mapped[PurchaseInvoice] = relationship(back_populates="lines"); item: Mapped[Item] = relationship()
