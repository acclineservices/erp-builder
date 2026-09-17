"""Validated API contracts for customer and supplier master data."""

from decimal import Decimal
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


class PartyInput(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    party_type: Literal["customer", "supplier", "both"] | None = None
    contact_person: str | None = Field(default=None, max_length=255)
    mobile_number: str | None = Field(default=None, max_length=32)
    alternate_mobile: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=320)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=128)
    state: str | None = Field(default=None, max_length=128)
    postal_code: str | None = Field(default=None, max_length=32)
    country: str | None = Field(default=None, max_length=128)
    gst_status: Literal["registered", "unregistered", "composition", "exempt"] = "unregistered"
    gstin: str | None = Field(default=None, max_length=32)
    pan: str | None = Field(default=None, max_length=16)
    opening_balance: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    opening_balance_type: Literal["debit", "credit"] = "debit"
    credit_limit: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    payment_terms_days: int | None = Field(default=None, ge=0, le=3650)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("gstin", "pan", "code", mode="before")
    @classmethod
    def normalize_uppercase(cls, value: object) -> object:
        return str(value).strip().upper() if value is not None and str(value).strip() else None

    @field_validator("email", "contact_person", "mobile_number", "alternate_mobile", "legal_name", "address_line1", "address_line2", "city", "state", "postal_code", "country", "notes", mode="before")
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        return str(value).strip() or None if value is not None else None

    @model_validator(mode="after")
    def validate_tax_identity(self) -> "PartyInput":
        if self.gst_status in {"registered", "composition"} and not self.gstin:
            raise ValueError("GSTIN is required for registered or composition parties.")
        if self.gstin and not GSTIN_PATTERN.fullmatch(self.gstin):
            raise ValueError("Enter a valid GSTIN format.")
        if self.pan and not PAN_PATTERN.fullmatch(self.pan):
            raise ValueError("Enter a valid PAN format.")
        return self


class PartyResponse(PartyInput):
    id: UUID
    customer_code: str | None
    supplier_code: str | None
    party_type: Literal["customer", "supplier", "both"]
    is_active: bool


class ActiveStatusRequest(BaseModel):
    is_active: bool
