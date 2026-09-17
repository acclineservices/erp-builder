"""P010 request and response schemas."""
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

class CommercialLineInput(BaseModel):
    item_id: UUID
    purchase_order_line_id: UUID | None = None
    goods_receipt_line_id: UUID | None = None
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    unit_rate: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100, max_digits=5, decimal_places=2)
    gst_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    description: str | None = Field(default=None, max_length=5000)

class PurchaseOrderInput(BaseModel):
    supplier_id: UUID; order_date: date; expected_delivery_date: date | None = None; branch_id: UUID | None = None; warehouse_id: UUID | None = None
    supplier_reference: str | None = Field(default=None, max_length=128); payment_terms: str | None = Field(default=None, max_length=255); notes: str | None = None; terms_conditions: str | None = None; round_off: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    lines: list[CommercialLineInput] = Field(min_length=1)

class GoodsReceiptLineInput(BaseModel):
    item_id: UUID; purchase_order_line_id: UUID | None = None; received_quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3); accepted_quantity: Decimal = Field(ge=0, max_digits=14, decimal_places=3); rejected_quantity: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=3); remarks: str | None = None
    @model_validator(mode="after")
    def quantities_match(self):
        if self.accepted_quantity + self.rejected_quantity != self.received_quantity: raise ValueError("Accepted and rejected quantities must equal received quantity.")
        return self

class GoodsReceiptInput(BaseModel):
    supplier_id: UUID; purchase_order_id: UUID | None = None; warehouse_id: UUID | None = None; receipt_date: date; supplier_challan_reference: str | None = Field(default=None, max_length=128); notes: str | None = None; lines: list[GoodsReceiptLineInput] = Field(min_length=1)

class PurchaseInvoiceInput(BaseModel):
    supplier_id: UUID; purchase_order_id: UUID | None = None; goods_receipt_id: UUID | None = None; supplier_invoice_number: str = Field(min_length=1, max_length=128); supplier_invoice_date: date; document_date: date; due_date: date | None = None; payment_terms: str | None = Field(default=None, max_length=255); notes: str | None = None; round_off: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2); lines: list[CommercialLineInput] = Field(min_length=1)

class StatusResponse(BaseModel):
    id: UUID; number: str; status: str
    model_config = {"from_attributes": True}
