"""Validated API contracts for P006 company structure management."""

from uuid import UUID

from pydantic import BaseModel, Field


class AddressFields(BaseModel):
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=128)
    state: str | None = Field(default=None, max_length=128)
    postal_code: str | None = Field(default=None, max_length=32)
    country: str | None = Field(default=None, max_length=128)


class CompanyUpdateRequest(AddressFields):
    legal_name: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    business_type: str = Field(default="proprietorship", min_length=2, max_length=64)
    gst_status: str | None = Field(default=None, max_length=32)
    gstin: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=32)
    logo_url: str | None = Field(default=None, max_length=1024)


class CompanyResponse(AddressFields):
    id: UUID
    business_name: str
    legal_name: str | None
    display_name: str | None
    business_type: str
    status: str
    gst_status: str | None
    gstin: str | None
    email: str | None
    phone: str | None
    logo_url: str | None
    setup_progress: int


class BranchInput(AddressFields):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=32)


class BranchResponse(BranchInput):
    id: UUID
    is_active: bool


class WarehouseInput(AddressFields):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    branch_id: UUID | None = None
    contact_person: str | None = Field(default=None, max_length=255)
    contact_number: str | None = Field(default=None, max_length=32)


class WarehouseResponse(WarehouseInput):
    id: UUID
    is_active: bool


class ActiveStatusRequest(BaseModel):
    is_active: bool
