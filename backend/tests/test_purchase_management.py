"""P010 purchase workflow, security, numbering, decimal and audit coverage."""
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import AuthenticationMethod, Company, Item, Party, Role, RoleAssignment, User, UserCompanyAccess, UserManagementAuditEvent
from app.services import administration as admin

@pytest.fixture
def database():
    engine=create_engine("sqlite+pysqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool);Base.metadata.create_all(engine);factory=sessionmaker(bind=engine,expire_on_commit=False)
    with factory() as session: yield session
@pytest.fixture
def client(database):
    def override(): yield database
    app.dependency_overrides[get_db]=override
    with TestClient(app) as test: yield test
    app.dependency_overrides.clear()
def setup(db, client):
    user=User(name="Purchase Admin",email="purchase@example.com",mobile_number="+919876543212",account_state="active",email_verified=True,mobile_verified=True);first=Company(business_name="Purchase One");second=Company(business_name="Purchase Two");db.add_all([user,first,second]);db.flush();db.add(AuthenticationMethod(user=user,method_type="email_password",credential_hash=hash_password("correct-password"),is_verified=True));db.add_all([UserCompanyAccess(user=user,company=first),UserCompanyAccess(user=user,company=second)]);admin.ensure_company_catalogue(db,first);admin.ensure_company_catalogue(db,second);role=db.scalar(select(Role).where(Role.company_id==first.id,Role.name=="Admin"));db.add(RoleAssignment(user=user,role=role,company_id=first.id));supplier=Party(company=first,party_type="supplier",display_name="Source Supply",supplier_code="SUP-0001");item=Item(company=first,name="Cable",code="ITEM-0001",item_type="goods",uom_code="MTR",purchase_price=10,selling_price=15,track_inventory=True);service=Item(company=first,name="Installation",code="ITEM-0002",item_type="service",uom_code="HR");foreign_supplier=Party(company=second,party_type="supplier",display_name="Foreign",supplier_code="SUP-0001");foreign_item=Item(company=second,name="Foreign item",code="ITEM-0001",item_type="goods",uom_code="PCS");db.add_all([supplier,item,service,foreign_supplier,foreign_item]);db.commit();client.post("/auth/login/email",json={"email":user.email,"password":"correct-password"});return first,second,user,supplier,item,service,foreign_supplier,foreign_item
def h(company): return {"X-Company-ID":str(company.id)}
def line(item, quantity=2, rate=10): return {"item_id":str(item.id),"quantity":quantity,"unit_rate":rate,"discount_percent":10,"gst_rate":5}
def test_purchase_documents_lifecycle_totals_audit_and_tenant(client,database):
    first,second,_,supplier,item,service,foreign_supplier,foreign_item=setup(database,client)
    payload={"supplier_id":str(supplier.id),"order_date":str(date.today()),"round_off":0,"lines":[line(item)]}
    po=client.post("/purchases/orders",headers=h(first),json=payload);assert po.status_code==201;body=po.json();assert body["number"]=="PO-0001" and float(body["grand_total"])==18.90
    assert client.post(f"/purchases/orders/{body['id']}/submit",headers=h(first)).json()["status"]=="submitted"
    assert client.post(f"/purchases/orders/{body['id']}/approve",headers=h(first)).json()["status"]=="approved"
    grn=client.post("/purchases/receipts",headers=h(first),json={"supplier_id":str(supplier.id),"purchase_order_id":body["id"],"receipt_date":str(date.today()),"lines":[{"item_id":str(item.id),"received_quantity":2,"accepted_quantity":2,"rejected_quantity":0}]});assert grn.status_code==201 and grn.json()["number"]=="GRN-0001"
    invoice=client.post("/purchases/invoices",headers=h(first),json={"supplier_id":str(supplier.id),"goods_receipt_id":grn.json()["id"],"supplier_invoice_number":"VENDOR-1","supplier_invoice_date":str(date.today()),"document_date":str(date.today()),"round_off":0,"lines":[line(item)]});assert invoice.status_code==201 and invoice.json()["number"]=="PI-0001"
    assert client.post("/purchases/receipts",headers=h(first),json={"supplier_id":str(supplier.id),"receipt_date":str(date.today()),"lines":[{"item_id":str(service.id),"received_quantity":1,"accepted_quantity":1}]}).status_code==422
    assert client.post("/purchases/orders",headers=h(first),json={**payload,"supplier_id":str(foreign_supplier.id)}).status_code==422
    assert client.post("/purchases/orders",headers=h(first),json={**payload,"lines":[line(foreign_item)]}).status_code==422
    assert client.get(f"/purchases/orders/{body['id']}",headers=h(second)).status_code==403
    assert {x.action for x in database.scalars(select(UserManagementAuditEvent)).all()} >= {"purchase_order_created","goods_receipt_created","purchase_invoice_created"}
def test_purchase_permission_rejection(client,database):
    first,_,user,supplier,item,*_=setup(database,client)
    for assignment in database.scalars(select(RoleAssignment).where(RoleAssignment.user_id==user.id)): database.delete(assignment)
    database.commit();assert client.get("/purchases/orders",headers=h(first)).status_code==403
