"""P010 purchase APIs, all guarded by company context and P007 permissions."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.dependencies import AuthorizedCompanyContext, require_authorized_company_context
from app.db.session import get_db
from app.schemas.purchases import GoodsReceiptInput, PurchaseInvoiceInput, PurchaseOrderInput
from app.services import administration as admin
from app.services import purchases as service
router=APIRouter(prefix="/purchases",tags=["purchases"])
def require(context,db,code):
    try: admin.require_permission(db,context.user,context.company,code)
    except admin.AdministrationForbidden as error: raise HTTPException(403,"You do not have permission for this purchase action.") from error
def serial(document):
    result={key:getattr(document,key) for key in ("id","number","status","supplier_id","purchase_order_id","goods_receipt_id","order_date","receipt_date","supplier_invoice_number","supplier_invoice_date","document_date","due_date","subtotal","discount_total","tax_total","round_off","grand_total") if hasattr(document,key)}
    result["supplier_name"]=document.supplier.display_name; result["lines"]=[]
    for line in document.lines:
        result["lines"].append({key:getattr(line,key) for key in ("id","item_id","item_name","item_code","description","uom_code","quantity","unit_rate","discount_percent","gst_rate","base_amount","discount_amount","tax_amount","line_total","ordered_quantity","received_quantity","accepted_quantity","rejected_quantity","remarks") if hasattr(line,key)})
    return result
def document_or_404(document):
    if not document: raise HTTPException(404,"The requested purchase document is not available in this company.")
    return document
def handle(work):
    try: return work()
    except service.PurchaseError as error: raise HTTPException(422,str(error)) from error
    except IntegrityError as error: raise HTTPException(409,"A duplicate supplier invoice reference or document number exists in this company.") from error
@router.get("/orders")
def list_orders(search:str|None=None,status_filter:str|None=Query(None,alias="status"),context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)): require(context,db,"purchases.view"); return [serial(x) for x in service.orders(db,context.company.id,search,status_filter)]
@router.get("/orders/{document_id}")
def get_order(document_id:UUID,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)): require(context,db,"purchases.view"); return serial(document_or_404(service.order(db,context.company.id,document_id)))
@router.post("/orders",status_code=status.HTTP_201_CREATED)
def create_order(payload:PurchaseOrderInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"purchases.create")
    def work():
        item=service.create_order(db,context.company,context.user,payload); db.commit(); db.refresh(item); return serial(service.order(db,context.company.id,item.id))
    return handle(work)
@router.put("/orders/{document_id}")
def update_order(document_id:UUID,payload:PurchaseOrderInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"purchases.edit"); document=document_or_404(service.order(db,context.company.id,document_id))
    def work(): service.update_order(db,context.company,context.user,document,payload);db.commit();return serial(service.order(db,context.company.id,document.id))
    return handle(work)
@router.post("/orders/{document_id}/{action}")
def transition_order(document_id:UUID,action:str,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    permission={"submit":"purchases.edit","approve":"purchases.approve","cancel":"purchases.cancel"}.get(action)
    if not permission: raise HTTPException(404,"Unknown purchase order action.")
    require(context,db,permission); document=document_or_404(service.order(db,context.company.id,document_id))
    def work(): service.transition_order(db,context.company,context.user,document,action);db.commit();return serial(document)
    return handle(work)
@router.get("/receipts")
def list_receipts(search:str|None=None,status_filter:str|None=Query(None,alias="status"),context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)): require(context,db,"purchases.view"); return [serial(x) for x in service.receipts(db,context.company.id,search,status_filter)]
@router.post("/receipts",status_code=status.HTTP_201_CREATED)
def create_receipt(payload:GoodsReceiptInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"purchases.create")
    def work(): item=service.create_receipt(db,context.company,context.user,payload);db.commit();return serial(service.receipt(db,context.company.id,item.id))
    return handle(work)
@router.post("/receipts/{document_id}/cancel")
def cancel_receipt(document_id:UUID,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"purchases.cancel");document=document_or_404(service.receipt(db,context.company.id,document_id))
    def work(): service.cancel_receipt(db,context.company,context.user,document);db.commit();return serial(document)
    return handle(work)
@router.get("/invoices")
def list_invoices(search:str|None=None,status_filter:str|None=Query(None,alias="status"),context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)): require(context,db,"purchases.view");return [serial(x) for x in service.invoices(db,context.company.id,search,status_filter)]
@router.post("/invoices",status_code=status.HTTP_201_CREATED)
def create_invoice(payload:PurchaseInvoiceInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"purchases.create")
    def work(): item=service.create_invoice(db,context.company,context.user,payload);db.commit();return serial(service.invoice(db,context.company.id,item.id))
    return handle(work)
@router.put("/invoices/{document_id}")
def update_invoice(document_id:UUID,payload:PurchaseInvoiceInput,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    require(context,db,"purchases.edit");document=document_or_404(service.invoice(db,context.company.id,document_id))
    def work(): service.update_invoice(db,context.company,context.user,document,payload);db.commit();return serial(service.invoice(db,context.company.id,document.id))
    return handle(work)
@router.post("/invoices/{document_id}/{action}")
def transition_invoice(document_id:UUID,action:str,context:AuthorizedCompanyContext=Depends(require_authorized_company_context),db:Session=Depends(get_db)):
    permission={"approve":"purchases.approve","cancel":"purchases.cancel"}.get(action)
    if not permission: raise HTTPException(404,"Unknown purchase invoice action.")
    require(context,db,permission);document=document_or_404(service.invoice(db,context.company.id,document_id))
    def work(): service.transition_invoice(db,context.company,context.user,document,action);db.commit();return serial(document)
    return handle(work)
