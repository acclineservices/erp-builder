"""P009 item master tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import AuthenticationMethod, Company, Role, RoleAssignment, User, UserCompanyAccess, UserManagementAuditEvent
from app.services import administration as admin

@pytest.fixture
def database():
    engine=create_engine("sqlite+pysqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool); Base.metadata.create_all(engine); factory=sessionmaker(bind=engine,expire_on_commit=False)
    with factory() as session: yield session

@pytest.fixture
def client(database):
    def override(): yield database
    app.dependency_overrides[get_db]=override
    with TestClient(app) as test: yield test
    app.dependency_overrides.clear()

def provision(db,client):
    user=User(name="Item Admin",email="items@example.com",mobile_number="+919876543211",account_state="active",email_verified=True,mobile_verified=True); first=Company(business_name="Items One"); second=Company(business_name="Items Two"); db.add_all([user,first,second]);db.flush();db.add(AuthenticationMethod(user=user,method_type="email_password",credential_hash=hash_password("correct-password"),is_verified=True));db.add_all([UserCompanyAccess(user=user,company=first),UserCompanyAccess(user=user,company=second)]);admin.ensure_company_catalogue(db,first);admin.ensure_company_catalogue(db,second);role=db.scalar(select(Role).where(Role.company_id==first.id,Role.name=="Admin"));db.add(RoleAssignment(user=user,role=role,company_id=first.id));db.commit();client.post("/auth/login/email",json={"email":user.email,"password":"correct-password"});return first,second,user

def header(company): return {"X-Company-ID":str(company.id)}
def goods(**values): return {"name":"Steel Rod","item_type":"goods","uom_code":"KG","track_inventory":True,"opening_stock":10,"purchase_price":12.5,"selling_price":20,"gst_rate":18,"hsn_sac_code":"7214",**values}

def test_item_category_codes_filters_audit_and_tenant(client,database):
    first,second,_=provision(database,client); category=client.post("/items/categories",headers=header(first),json={"name":"Metals","code":"MET","description":None}); assert category.status_code==201
    created=client.post("/items",headers=header(first),json=goods(category_id=category.json()["id"],barcode="ABC-1")); assert created.status_code==201; body=created.json(); assert body["code"]=="ITEM-0001" and body["selling_price"]=="20.00"
    assert client.post("/items",headers=header(first),json=goods(name="Duplicate",barcode="ABC-1")).status_code==409
    assert client.get(f"/items/{body['id']}",headers=header(second)).status_code==403
    assert len(client.get("/items?search=ABC-1&item_type=goods&tracked=true",headers=header(first)).json())==1
    assert client.patch(f"/items/{body['id']}/status",headers=header(first),json={"is_active":False}).json()["is_active"] is False
    assert "item_created" in {event.action for event in database.scalars(select(UserManagementAuditEvent)).all()}

def test_service_validation_and_permission(client,database):
    first,_,user=provision(database,client); service=client.post("/items",headers=header(first),json={"name":"Installation","item_type":"service","uom_code":"HR","selling_price":500,"gst_rate":18}); assert service.status_code==201
    assert client.post("/items",headers=header(first),json={"name":"Bad service","item_type":"service","uom_code":"HR","track_inventory":True}).status_code==422
    for assignment in database.scalars(select(RoleAssignment).where(RoleAssignment.user_id==user.id)): database.delete(assignment)
    database.commit(); assert client.get("/items",headers=header(first)).status_code==403
