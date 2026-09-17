"""P010 tenant-scoped purchase operations and authoritative decimal totals."""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload
from app.models import Branch, Company, GoodsReceipt, GoodsReceiptLine, Item, Party, PurchaseDocumentSequence, PurchaseInvoice, PurchaseInvoiceLine, PurchaseOrder, PurchaseOrderLine, User, Warehouse
from app.models.identity import UserManagementAuditEvent
from app.schemas.purchases import GoodsReceiptInput, PurchaseInvoiceInput, PurchaseOrderInput

class PurchaseError(ValueError): pass
MONEY = Decimal("0.01")
def _money(value: Decimal) -> Decimal: return value.quantize(MONEY, rounding=ROUND_HALF_UP)
def _next_number(db: Session, company_id: UUID, kind: str) -> str:
    sequence = db.scalar(select(PurchaseDocumentSequence).where(PurchaseDocumentSequence.company_id == company_id, PurchaseDocumentSequence.document_type == kind).with_for_update())
    if sequence is None:
        sequence = PurchaseDocumentSequence(company_id=company_id, document_type=kind, next_value=1); db.add(sequence); db.flush()
    current = sequence.next_value; sequence.next_value += 1
    return f"{kind}-{current:04d}"
def _audit(db: Session, company: Company, actor: User, action: str, document: object) -> None:
    db.add(UserManagementAuditEvent(company_id=company.id, actor_user_id=actor.id, action=action, details=f"purchase:{getattr(document, 'id')}"))
def _supplier(db: Session, company_id: UUID, supplier_id: UUID) -> Party:
    supplier = db.scalar(select(Party).where(Party.id == supplier_id, Party.company_id == company_id, Party.supplier_code.is_not(None), Party.is_active.is_(True)))
    if not supplier: raise PurchaseError("The supplier is not active or is not available in this company.")
    return supplier
def _item(db: Session, company_id: UUID, item_id: UUID) -> Item:
    item = db.scalar(select(Item).where(Item.id == item_id, Item.company_id == company_id, Item.is_active.is_(True)))
    if not item: raise PurchaseError("The item is not active or is not available in this company.")
    return item
def _warehouse(db: Session, company_id: UUID, warehouse_id: UUID | None) -> Warehouse | None:
    if warehouse_id is None: return None
    warehouse = db.scalar(select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.company_id == company_id, Warehouse.is_active.is_(True)))
    if not warehouse: raise PurchaseError("The warehouse is not active or is not available in this company.")
    return warehouse
def _branch(db: Session, company_id: UUID, branch_id: UUID | None) -> Branch | None:
    if branch_id is None: return None
    branch = db.scalar(select(Branch).where(Branch.id == branch_id, Branch.company_id == company_id, Branch.is_active.is_(True)))
    if not branch: raise PurchaseError("The branch is not active or is not available in this company.")
    return branch
def _commercial_lines(db: Session, company_id: UUID, values: list, owner: object, line_type: type) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    subtotal=discount_total=tax_total=grand=Decimal("0")
    for value in values:
        item=_item(db,company_id,value.item_id); base=_money(value.quantity * value.unit_rate); discount=_money(base * value.discount_percent / 100); taxable=base-discount; tax=_money(taxable * (value.gst_rate or Decimal("0")) / 100); total=taxable+tax
        source = {}
        if line_type is PurchaseInvoiceLine:
            source = _invoice_line_sources(db, company_id, value, item.id)
        line=line_type(item=item,item_name=item.display_name or item.name,item_code=item.code,description=value.description if value.description is not None else item.description,uom_code=item.uom_code,quantity=value.quantity,unit_rate=value.unit_rate,discount_percent=value.discount_percent,gst_rate=value.gst_rate if value.gst_rate is not None else item.gst_rate,base_amount=base,discount_amount=discount,tax_amount=tax,line_total=total, **source)
        if isinstance(owner, PurchaseOrder): line.order=owner
        else: line.invoice=owner
        db.add(line); subtotal+=base; discount_total+=discount; tax_total+=tax; grand+=total
    return _money(subtotal),_money(discount_total),_money(tax_total),_money(grand)
def _apply_totals(document: object, values: list, db: Session, company_id: UUID, line_type: type, round_off: Decimal) -> None:
    subtotal,discount,tax,total=_commercial_lines(db,company_id,values,document,line_type)
    document.subtotal,document.discount_total,document.tax_total,document.round_off,document.grand_total=subtotal,discount,tax,_money(round_off),_money(total+round_off)

def _invoice_line_sources(db: Session, company_id: UUID, value: object, item_id: UUID) -> dict:
    po_line_id = getattr(value, "purchase_order_line_id", None)
    grn_line_id = getattr(value, "goods_receipt_line_id", None)
    po_line = db.get(PurchaseOrderLine, po_line_id) if po_line_id else None
    grn_line = db.get(GoodsReceiptLine, grn_line_id) if grn_line_id else None
    if po_line and (po_line.item_id != item_id or po_line.order.company_id != company_id): raise PurchaseError("The purchase order line is not available in this company.")
    if grn_line and (grn_line.item_id != item_id or grn_line.receipt.company_id != company_id): raise PurchaseError("The goods receipt line is not available in this company.")
    if po_line_id and not po_line: raise PurchaseError("The purchase order line is not available in this company.")
    if grn_line_id and not grn_line: raise PurchaseError("The goods receipt line is not available in this company.")
    if po_line and grn_line and grn_line.purchase_order_line_id != po_line.id: raise PurchaseError("The selected receipt line does not belong to the purchase order line.")
    return {"purchase_order_line_id": po_line_id, "goods_receipt_line_id": grn_line_id}

def orders(db: Session, company_id: UUID, search: str | None = None, status: str | None = None) -> list[PurchaseOrder]:
    query=select(PurchaseOrder).options(selectinload(PurchaseOrder.lines),selectinload(PurchaseOrder.supplier)).where(PurchaseOrder.company_id==company_id)
    if status: query=query.where(PurchaseOrder.status==status)
    if search: query=query.join(PurchaseOrder.supplier).where(or_(PurchaseOrder.number.ilike(f"%{search.strip()}%"),Party.display_name.ilike(f"%{search.strip()}%")))
    return list(db.scalars(query.order_by(PurchaseOrder.created_at.desc())).unique().all())
def order(db: Session, company_id: UUID, document_id: UUID) -> PurchaseOrder | None: return db.scalar(select(PurchaseOrder).options(selectinload(PurchaseOrder.lines),selectinload(PurchaseOrder.supplier)).where(PurchaseOrder.id==document_id,PurchaseOrder.company_id==company_id))
def create_order(db: Session, company: Company, actor: User, payload: PurchaseOrderInput) -> PurchaseOrder:
    _supplier(db,company.id,payload.supplier_id); _branch(db,company.id,payload.branch_id); _warehouse(db,company.id,payload.warehouse_id)
    document=PurchaseOrder(company=company,supplier_id=payload.supplier_id,branch_id=payload.branch_id,warehouse_id=payload.warehouse_id,number=_next_number(db,company.id,"PO"),order_date=payload.order_date,expected_delivery_date=payload.expected_delivery_date,supplier_reference=payload.supplier_reference,payment_terms=payload.payment_terms,notes=payload.notes,terms_conditions=payload.terms_conditions)
    db.add(document); db.flush(); _apply_totals(document,payload.lines,db,company.id,PurchaseOrderLine,payload.round_off); db.flush(); _audit(db,company,actor,"purchase_order_created",document); return document
def update_order(db: Session, company: Company, actor: User, document: PurchaseOrder, payload: PurchaseOrderInput) -> PurchaseOrder:
    if document.status != "draft": raise PurchaseError("Only draft purchase orders can be edited.")
    _supplier(db,company.id,payload.supplier_id); _branch(db,company.id,payload.branch_id); _warehouse(db,company.id,payload.warehouse_id)
    for key,value in payload.model_dump(exclude={"lines","round_off"}).items(): setattr(document,key,value)
    for line in list(document.lines): db.delete(line)
    db.flush(); _apply_totals(document,payload.lines,db,company.id,PurchaseOrderLine,payload.round_off); db.flush(); _audit(db,company,actor,"purchase_order_updated",document); return document
def transition_order(db: Session, company: Company, actor: User, document: PurchaseOrder, action: str) -> PurchaseOrder:
    allowed={"submit":({"draft"},"submitted"),"approve":({"submitted"},"approved"),"cancel":({"draft","submitted","approved","partially_received"},"cancelled")}
    old,new=allowed[action]
    if document.status not in old: raise PurchaseError(f"This purchase order cannot be {action}ed from its current status.")
    document.status=new; _audit(db,company,actor,f"purchase_order_{action}ed",document); return document

def receipts(db: Session, company_id: UUID, search: str | None = None, status: str | None = None) -> list[GoodsReceipt]:
    query=select(GoodsReceipt).options(selectinload(GoodsReceipt.lines),selectinload(GoodsReceipt.supplier)).where(GoodsReceipt.company_id==company_id)
    if status: query=query.where(GoodsReceipt.status==status)
    if search: query=query.join(GoodsReceipt.supplier).where(or_(GoodsReceipt.number.ilike(f"%{search.strip()}%"),Party.display_name.ilike(f"%{search.strip()}%")))
    return list(db.scalars(query.order_by(GoodsReceipt.created_at.desc())).unique().all())
def receipt(db: Session, company_id: UUID, document_id: UUID) -> GoodsReceipt | None: return db.scalar(select(GoodsReceipt).options(selectinload(GoodsReceipt.lines),selectinload(GoodsReceipt.supplier),selectinload(GoodsReceipt.purchase_order)).where(GoodsReceipt.id==document_id,GoodsReceipt.company_id==company_id))
def _received_before(db: Session, po_line_id: UUID, exclude_receipt_id: UUID | None = None) -> Decimal:
    query=select(GoodsReceiptLine.received_quantity).join(GoodsReceiptLine.receipt).where(GoodsReceiptLine.purchase_order_line_id==po_line_id,GoodsReceipt.status=="received")
    if exclude_receipt_id: query=query.where(GoodsReceipt.id != exclude_receipt_id)
    return sum(db.scalars(query).all(), Decimal("0"))
def _sync_order_receipt_status(db: Session, order_document: PurchaseOrder) -> None:
    goods=[line for line in order_document.lines if line.item.item_type=="goods"]
    if not goods: return
    complete=all(_received_before(db,line.id) >= line.quantity for line in goods)
    any_received=any(_received_before(db,line.id) > 0 for line in goods)
    if complete: order_document.status="received"
    elif any_received: order_document.status="partially_received"
    elif order_document.status in {"partially_received","received"}: order_document.status="approved"
def _set_receipt_lines(db: Session, company: Company, document: GoodsReceipt, payload: GoodsReceiptInput) -> None:
    linked=order(db,company.id,payload.purchase_order_id) if payload.purchase_order_id else None
    if payload.purchase_order_id and not linked: raise PurchaseError("The purchase order is not available in this company.")
    if linked and linked.supplier_id != payload.supplier_id: raise PurchaseError("The purchase order supplier must match the receipt supplier.")
    po_lines={line.id:line for line in linked.lines} if linked else {}
    for value in payload.lines:
        item=_item(db,company.id,value.item_id)
        if item.item_type != "goods": raise PurchaseError("Goods receipts are only for Goods items; services do not require a GRN.")
        po_line=po_lines.get(value.purchase_order_line_id) if value.purchase_order_line_id else None
        if value.purchase_order_line_id and (not po_line or po_line.item_id != item.id): raise PurchaseError("The selected purchase order line is not valid for this receipt.")
        if po_line and value.received_quantity > po_line.quantity - _received_before(db,po_line.id,document.id): raise PurchaseError("Received quantity exceeds the remaining purchase order quantity.")
        db.add(GoodsReceiptLine(receipt=document,purchase_order_line_id=value.purchase_order_line_id,item=item,item_name=item.display_name or item.name,item_code=item.code,uom_code=item.uom_code,ordered_quantity=po_line.quantity if po_line else None,received_quantity=value.received_quantity,accepted_quantity=value.accepted_quantity,rejected_quantity=value.rejected_quantity,remarks=value.remarks))
def create_receipt(db: Session, company: Company, actor: User, payload: GoodsReceiptInput) -> GoodsReceipt:
    _supplier(db,company.id,payload.supplier_id); _warehouse(db,company.id,payload.warehouse_id)
    document=GoodsReceipt(company=company,supplier_id=payload.supplier_id,purchase_order_id=payload.purchase_order_id,warehouse_id=payload.warehouse_id,number=_next_number(db,company.id,"GRN"),receipt_date=payload.receipt_date,supplier_challan_reference=payload.supplier_challan_reference,notes=payload.notes,status="draft")
    db.add(document); db.flush(); _set_receipt_lines(db,company,document,payload)
    db.flush(); _audit(db,company,actor,"goods_receipt_created",document); return document
def update_receipt(db: Session, company: Company, actor: User, document: GoodsReceipt, payload: GoodsReceiptInput) -> GoodsReceipt:
    if document.status != "draft": raise PurchaseError("Only draft goods receipts can be edited.")
    _supplier(db,company.id,payload.supplier_id); _warehouse(db,company.id,payload.warehouse_id)
    for key,value in payload.model_dump(exclude={"lines"}).items(): setattr(document,key,value)
    for line in list(document.lines): db.delete(line)
    db.flush(); _set_receipt_lines(db,company,document,payload); db.flush(); _audit(db,company,actor,"goods_receipt_updated",document); return document
def receive_receipt(db: Session, company: Company, actor: User, document: GoodsReceipt) -> GoodsReceipt:
    if document.status != "draft": raise PurchaseError("Only draft goods receipts can be received.")
    for line in document.lines:
        if line.purchase_order_line and line.received_quantity > line.purchase_order_line.quantity - _received_before(db, line.purchase_order_line_id, document.id):
            raise PurchaseError("Received quantity exceeds the remaining purchase order quantity.")
    document.status="received"
    if document.purchase_order: _sync_order_receipt_status(db,document.purchase_order)
    _audit(db,company,actor,"goods_receipt_received",document); return document
def cancel_receipt(db: Session, company: Company, actor: User, document: GoodsReceipt) -> GoodsReceipt:
    if document.status=="cancelled": raise PurchaseError("This goods receipt is already cancelled.")
    document.status="cancelled"
    if document.purchase_order: _sync_order_receipt_status(db,document.purchase_order)
    _audit(db,company,actor,"goods_receipt_cancelled",document); return document

def invoices(db: Session, company_id: UUID, search: str | None = None, status: str | None = None) -> list[PurchaseInvoice]:
    query=select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines),selectinload(PurchaseInvoice.supplier)).where(PurchaseInvoice.company_id==company_id)
    if status: query=query.where(PurchaseInvoice.status==status)
    if search: query=query.join(PurchaseInvoice.supplier).where(or_(PurchaseInvoice.number.ilike(f"%{search.strip()}%"),PurchaseInvoice.supplier_invoice_number.ilike(f"%{search.strip()}%"),Party.display_name.ilike(f"%{search.strip()}%")))
    return list(db.scalars(query.order_by(PurchaseInvoice.created_at.desc())).unique().all())
def invoice(db: Session, company_id: UUID, document_id: UUID) -> PurchaseInvoice | None: return db.scalar(select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines),selectinload(PurchaseInvoice.supplier)).where(PurchaseInvoice.id==document_id,PurchaseInvoice.company_id==company_id))
def _validate_links(db: Session, company_id: UUID, supplier_id: UUID, po_id: UUID | None, grn_id: UUID | None) -> None:
    po=order(db,company_id,po_id) if po_id else None; grn=receipt(db,company_id,grn_id) if grn_id else None
    if po_id and not po: raise PurchaseError("The linked purchase order is not available in this company.")
    if grn_id and not grn: raise PurchaseError("The linked goods receipt is not available in this company.")
    if grn and grn.status != "received": raise PurchaseError("Only received goods receipts can be linked to a purchase invoice.")
    if (po and po.supplier_id != supplier_id) or (grn and grn.supplier_id != supplier_id): raise PurchaseError("Linked documents must have the same supplier.")
    if po and grn and grn.purchase_order_id != po.id: raise PurchaseError("The linked goods receipt does not belong to the selected purchase order.")
def create_invoice(db: Session, company: Company, actor: User, payload: PurchaseInvoiceInput) -> PurchaseInvoice:
    _supplier(db,company.id,payload.supplier_id); _validate_links(db,company.id,payload.supplier_id,payload.purchase_order_id,payload.goods_receipt_id)
    document=PurchaseInvoice(company=company,number=_next_number(db,company.id,"PI"),**payload.model_dump(exclude={"lines","round_off"})); db.add(document); db.flush(); _apply_totals(document,payload.lines,db,company.id,PurchaseInvoiceLine,payload.round_off); db.flush(); _audit(db,company,actor,"purchase_invoice_created",document); return document
def update_invoice(db: Session, company: Company, actor: User, document: PurchaseInvoice, payload: PurchaseInvoiceInput) -> PurchaseInvoice:
    if document.status!="draft": raise PurchaseError("Only draft purchase invoices can be edited.")
    _supplier(db,company.id,payload.supplier_id); _validate_links(db,company.id,payload.supplier_id,payload.purchase_order_id,payload.goods_receipt_id)
    for key,value in payload.model_dump(exclude={"lines","round_off"}).items(): setattr(document,key,value)
    for line in list(document.lines): db.delete(line)
    db.flush(); _apply_totals(document,payload.lines,db,company.id,PurchaseInvoiceLine,payload.round_off); db.flush(); _audit(db,company,actor,"purchase_invoice_updated",document); return document
def transition_invoice(db: Session, company: Company, actor: User, document: PurchaseInvoice, action: str) -> PurchaseInvoice:
    target={"approve":"approved","cancel":"cancelled"}[action]
    if document.status != "draft": raise PurchaseError("Only draft purchase invoices can be approved or cancelled.")
    document.status=target; _audit(db,company,actor,f"purchase_invoice_{action}ed",document); return document
