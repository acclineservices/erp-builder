"""P009 item-master API contracts."""
from decimal import Decimal
import re
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator

UOMS = ("PCS", "NOS", "KG", "GM", "LTR", "ML", "MTR", "BOX", "PACK", "SET", "HR")
GST_RATES = {Decimal("0"), Decimal("5"), Decimal("12"), Decimal("18"), Decimal("28")}

class CategoryInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=4000)
    @field_validator("code", mode="before")
    @classmethod
    def code_upper(cls, value: object) -> object: return str(value).strip().upper() or None if value is not None else None

class CategoryResponse(CategoryInput):
    id: UUID
    is_active: bool

class StatusInput(BaseModel): is_active: bool

class ItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    item_type: Literal["goods", "service"]
    description: str | None = Field(default=None, max_length=4000)
    category_id: UUID | None = None
    uom_code: str = "PCS"
    hsn_sac_code: str | None = Field(default=None, max_length=16)
    barcode: str | None = Field(default=None, max_length=128)
    purchase_price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    selling_price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    gst_rate: Decimal | None = Field(default=None, max_digits=5, decimal_places=2)
    track_inventory: bool = False
    opening_stock: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=3)
    reorder_level: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=3)
    default_warehouse_id: UUID | None = None
    image_url: str | None = Field(default=None, max_length=1024)
    notes: str | None = Field(default=None, max_length=4000)
    @field_validator("code", "barcode", "hsn_sac_code", mode="before")
    @classmethod
    def clean_codes(cls, value: object) -> object: return str(value).strip().upper() or None if value is not None else None
    @field_validator("uom_code", mode="before")
    @classmethod
    def valid_uom(cls, value: object) -> str:
        code = str(value).strip().upper()
        if code not in UOMS: raise ValueError("Choose a supported unit of measure.")
        return code
    @model_validator(mode="after")
    def validate_item(self) -> "ItemInput":
        if self.gst_rate is not None and self.gst_rate not in GST_RATES: raise ValueError("Choose a supported GST rate.")
        if self.hsn_sac_code and not re.fullmatch(r"[0-9A-Z]{4,12}", self.hsn_sac_code): raise ValueError("Enter a valid HSN or SAC code.")
        if self.item_type == "service" and (self.track_inventory or self.opening_stock or self.reorder_level is not None or self.default_warehouse_id is not None): raise ValueError("Services cannot use inventory fields.")
        return self

class ItemResponse(ItemInput):
    id: UUID
    code: str
    category_name: str | None = None
    is_active: bool
