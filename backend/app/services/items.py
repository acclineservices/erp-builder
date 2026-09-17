"""Tenant-safe P009 item and category operations."""
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models import Company, Item, ItemCategory, ItemCodeSequence, User, Warehouse
from app.models.identity import UserManagementAuditEvent
from app.schemas.items import CategoryInput, ItemInput

class ItemError(ValueError): pass

def _audit(db: Session, company: Company, user: User, action: str, item_id: UUID) -> None: db.add(UserManagementAuditEvent(company_id=company.id, actor_user_id=user.id, action=action, details=f"item:{item_id}"))
def _next_code(db: Session, company_id: UUID) -> str:
    sequence = db.scalar(select(ItemCodeSequence).where(ItemCodeSequence.company_id == company_id).with_for_update())
    if sequence is None: sequence = ItemCodeSequence(company_id=company_id); db.add(sequence); db.flush()
    value = sequence.next_value; sequence.next_value += 1; return f"ITEM-{value:04d}"
def category(db: Session, company_id: UUID, category_id: UUID) -> ItemCategory | None: return db.scalar(select(ItemCategory).where(ItemCategory.id == category_id, ItemCategory.company_id == company_id))
def item(db: Session, company_id: UUID, item_id: UUID) -> Item | None: return db.scalar(select(Item).where(Item.id == item_id, Item.company_id == company_id))
def categories(db: Session, company_id: UUID, active: bool | None = None) -> list[ItemCategory]:
    q=select(ItemCategory).where(ItemCategory.company_id==company_id)
    if active is not None: q=q.where(ItemCategory.is_active.is_(active))
    return list(db.scalars(q.order_by(ItemCategory.name)).all())
def items(db: Session, company_id: UUID, search: str | None=None, active: bool|None=None, item_type: str|None=None, category_id: UUID|None=None, tracked: bool|None=None) -> list[Item]:
    q=select(Item).where(Item.company_id==company_id)
    if search: q=q.where(or_(*[field.ilike(f"%{search.strip()}%") for field in (Item.name,Item.code,Item.barcode,Item.hsn_sac_code)]))
    if active is not None: q=q.where(Item.is_active.is_(active))
    if item_type in {"goods","service"}: q=q.where(Item.item_type==item_type)
    if category_id: q=q.where(Item.category_id==category_id)
    if tracked is not None: q=q.where(Item.track_inventory.is_(tracked))
    return list(db.scalars(q.order_by(Item.name,Item.created_at)).all())
def create_category(db: Session, company: Company, user: User, payload: CategoryInput) -> ItemCategory:
    record=ItemCategory(company=company, **payload.model_dump()); db.add(record); db.flush(); _audit(db,company,user,"item_category_created",record.id); return record
def update_category(db: Session, company: Company, user: User, record: ItemCategory, payload: CategoryInput) -> ItemCategory:
    for key,value in payload.model_dump().items(): setattr(record,key,value)
    db.flush(); _audit(db,company,user,"item_category_updated",record.id); return record
def _validate_refs(db: Session, company: Company, payload: ItemInput) -> None:
    if payload.category_id:
        record=category(db,company.id,payload.category_id)
        if record is None or not record.is_active: raise ItemError("The selected category is not available in this company.")
    if payload.default_warehouse_id:
        warehouse=db.get(Warehouse,payload.default_warehouse_id)
        if warehouse is None or warehouse.company_id!=company.id or not warehouse.is_active: raise ItemError("The selected warehouse is not available in this company.")
def create_item(db: Session, company: Company, user: User, payload: ItemInput) -> Item:
    _validate_refs(db,company,payload); values=payload.model_dump(exclude={"code"}); record=Item(company=company,code=payload.code or _next_code(db,company.id),**values); db.add(record); db.flush(); _audit(db,company,user,"item_created",record.id); return record
def update_item(db: Session, company: Company, user: User, record: Item, payload: ItemInput) -> Item:
    _validate_refs(db,company,payload)
    for key,value in payload.model_dump().items():
        if key!="code": setattr(record,key,value)
    if payload.code: record.code=payload.code
    db.flush(); _audit(db,company,user,"item_updated",record.id); return record
def set_status(db: Session, company: Company, user: User, record: Item|ItemCategory, active: bool, category_record: bool=False) -> None:
    record.is_active=active; db.flush(); _audit(db,company,user, f"item_category_{'activated' if active else 'deactivated'}" if category_record else f"item_{'activated' if active else 'deactivated'}", record.id)
