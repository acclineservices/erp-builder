"""Tenant-scoped organization management operations.

P006 authorizes an active UserCompanyAccess grant. P007 can add role-level policy
checks at this service boundary without changing route or tenancy behavior.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Branch, Company, Warehouse
from app.schemas.organization import BranchInput, CompanyUpdateRequest, WarehouseInput


def setup_progress(company: Company) -> int:
    completed = sum(bool(value) for value in (company.legal_name, company.display_name, company.email, company.phone, company.address_line1))
    return round(completed / 5 * 100)


def update_company(company: Company, payload: CompanyUpdateRequest) -> Company:
    for field, value in payload.model_dump().items():
        setattr(company, field, value.strip() if isinstance(value, str) else value)
    return company


def branches_for_company(database: Session, company_id: UUID) -> list[Branch]:
    return list(database.scalars(select(Branch).where(Branch.company_id == company_id).order_by(Branch.name)))


def branch_for_company(database: Session, company_id: UUID, branch_id: UUID) -> Branch | None:
    return database.scalar(select(Branch).where(Branch.id == branch_id, Branch.company_id == company_id))


def create_branch(company: Company, payload: BranchInput) -> Branch:
    values = payload.model_dump()
    return Branch(company=company, **{field: value.strip() if isinstance(value, str) else value for field, value in values.items()})


def update_branch(branch: Branch, payload: BranchInput) -> Branch:
    for field, value in payload.model_dump().items():
        setattr(branch, field, value.strip() if isinstance(value, str) else value)
    return branch


def warehouses_for_company(database: Session, company_id: UUID) -> list[Warehouse]:
    return list(database.scalars(select(Warehouse).where(Warehouse.company_id == company_id).order_by(Warehouse.name)))


def warehouse_for_company(database: Session, company_id: UUID, warehouse_id: UUID) -> Warehouse | None:
    return database.scalar(select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.company_id == company_id))


def validate_warehouse_branch(database: Session, company_id: UUID, branch_id: UUID | None) -> None:
    if branch_id is not None and branch_for_company(database, company_id, branch_id) is None:
        raise ValueError("The selected branch is not available in this company.")


def create_warehouse(database: Session, company: Company, payload: WarehouseInput) -> Warehouse:
    validate_warehouse_branch(database, company.id, payload.branch_id)
    values = payload.model_dump()
    warehouse = Warehouse(company=company, **{field: value.strip() if isinstance(value, str) else value for field, value in values.items()})
    database.add(warehouse)
    return warehouse


def update_warehouse(database: Session, warehouse: Warehouse, payload: WarehouseInput) -> Warehouse:
    validate_warehouse_branch(database, warehouse.company_id, payload.branch_id)
    for field, value in payload.model_dump().items():
        setattr(warehouse, field, value.strip() if isinstance(value, str) else value)
    return warehouse
