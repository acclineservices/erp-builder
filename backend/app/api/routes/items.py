"""P009 item-master routes."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.dependencies import AuthorizedCompanyContext, require_authorized_company_context
from app.db.session import get_db
from app.models import Item, ItemCategory
from app.schemas.items import CategoryInput, CategoryResponse, ItemInput, ItemResponse, StatusInput, UOMS
from app.services import administration as administration_service
from app.services import items as service

router=APIRouter(prefix="/items",tags=["item master"])
def require(context: AuthorizedCompanyContext, db: Session, permission: str) -> None:
    try: administration_service.require_permission(db,context.user,context.company,permission)
    except administration_service.AdministrationForbidden as error: raise HTTPException(403,"You do not have permission for this item action.") from error
def category_response(record: ItemCategory) -> CategoryResponse: return CategoryResponse(id=record.id,name=record.name,code=record.code,description=record.description,is_active=record.is_active)
def item_response(record: Item) -> ItemResponse:
    return ItemResponse(id=record.id,name=record.name,display_name=record.display_name,code=record.code,item_type=record.item_type,description=record.description,category_id=record.category_id,category_name=record.category.name if record.category else None,uom_code=record.uom_code,hsn_sac_code=record.hsn_sac_code,barcode=record.barcode,purchase_price=record.purchase_price,selling_price=record.selling_price,gst_rate=record.gst_rate,track_inventory=record.track_inventory,opening_stock=record.opening_stock,reorder_level=record.reorder_level,default_warehouse_id=record.default_warehouse_id,image_url=record.image_url,notes=record.notes,is_active=record.is_active)
def conflict(error: IntegrityError) -> HTTPException: return HTTPException(409,"An item, barcode, or category code with that value already exists in this company.")
@router.get("/uoms")
def uoms(context: AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)) -> list[str]: require(context,db,"items.view"); return list(UOMS)
@router.get("/categories",response_model=list[CategoryResponse])
def list_categories(active: bool|None=None,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)): require(context,db,"items.view"); return [category_response(x) for x in service.categories(db,context.company.id,active)]
@router.post("/categories",response_model=CategoryResponse,status_code=201)
def create_category(payload:CategoryInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"items.create")
    try: record=service.create_category(db,context.company,context.user,payload); db.commit(); return category_response(record)
    except IntegrityError as error: db.rollback(); raise conflict(error) from error
@router.put("/categories/{category_id}",response_model=CategoryResponse)
def update_category(category_id:UUID,payload:CategoryInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"items.edit"); record=service.category(db,context.company.id,category_id)
    if not record: raise HTTPException(404,"The requested category is not available in this company.")
    try: record=service.update_category(db,context.company,context.user,record,payload); db.commit(); return category_response(record)
    except IntegrityError as error: db.rollback(); raise conflict(error) from error
@router.patch("/categories/{category_id}/status",response_model=CategoryResponse)
def category_status(category_id:UUID,payload:StatusInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"items.deactivate"); record=service.category(db,context.company.id,category_id)
    if not record: raise HTTPException(404,"The requested category is not available in this company.")
    service.set_status(db,context.company,context.user,record,payload.is_active,True); db.commit(); return category_response(record)
@router.get("",response_model=list[ItemResponse])
def list_items(search:str|None=None,active:bool|None=None,item_type:str|None=Query(None,pattern="^(goods|service)$"),category_id:UUID|None=None,tracked:bool|None=None,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"items.view"); return [item_response(x) for x in service.items(db,context.company.id,search,active,item_type,category_id,tracked)]
@router.get("/{item_id}",response_model=ItemResponse)
def get_item(item_id:UUID,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"items.view"); record=service.item(db,context.company.id,item_id)
    if not record: raise HTTPException(404,"The requested item is not available in this company.")
    return item_response(record)
@router.post("",response_model=ItemResponse,status_code=201)
def create_item(payload:ItemInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"items.create")
    try: record=service.create_item(db,context.company,context.user,payload); db.commit(); db.refresh(record); return item_response(record)
    except service.ItemError as error: db.rollback(); raise HTTPException(422,str(error)) from error
    except IntegrityError as error: db.rollback(); raise conflict(error) from error
@router.put("/{item_id}",response_model=ItemResponse)
def update_item(item_id:UUID,payload:ItemInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"items.edit"); record=service.item(db,context.company.id,item_id)
    if not record: raise HTTPException(404,"The requested item is not available in this company.")
    try: record=service.update_item(db,context.company,context.user,record,payload); db.commit(); db.refresh(record); return item_response(record)
    except service.ItemError as error: db.rollback(); raise HTTPException(422,str(error)) from error
    except IntegrityError as error: db.rollback(); raise conflict(error) from error
@router.patch("/{item_id}/status",response_model=ItemResponse)
def item_status(item_id:UUID,payload:StatusInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"items.deactivate"); record=service.item(db,context.company.id,item_id)
    if not record: raise HTTPException(404,"The requested item is not available in this company.")
    service.set_status(db,context.company,context.user,record,payload.is_active); db.commit(); db.refresh(record); return item_response(record)
