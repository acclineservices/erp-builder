"""Authenticated company, branch, and warehouse API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DatabaseSession

from app.api.dependencies import AuthorizedCompanyContext, require_authorized_company_context
from app.db.session import get_db
from app.models import Branch, Warehouse
from app.schemas.organization import (
    ActiveStatusRequest,
    BranchInput,
    BranchResponse,
    CompanyResponse,
    CompanyUpdateRequest,
    WarehouseInput,
    WarehouseResponse,
)
from app.services import organization as organization_service

router = APIRouter(prefix="/organization", tags=["organization"])


def company_response(context: AuthorizedCompanyContext) -> CompanyResponse:
    company = context.company
    return CompanyResponse(
        id=company.id,
        business_name=company.business_name,
        legal_name=company.legal_name,
        display_name=company.display_name,
        business_type=company.business_type,
        status=company.status,
        gst_status=company.gst_status,
        gstin=company.gstin,
        email=company.email,
        phone=company.phone,
        address_line1=company.address_line1,
        address_line2=company.address_line2,
        city=company.city,
        state=company.state,
        postal_code=company.postal_code,
        country=company.country,
        logo_url=company.logo_url,
        setup_progress=organization_service.setup_progress(company),
    )


def branch_response(branch: Branch) -> BranchResponse:
    return BranchResponse(**{column: getattr(branch, column) for column in BranchResponse.model_fields})


def warehouse_response(warehouse: Warehouse) -> WarehouseResponse:
    return WarehouseResponse(**{column: getattr(warehouse, column) for column in WarehouseResponse.model_fields})


def not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The requested organization record was not found.")


def conflict() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A record with those values already exists in this company.")


@router.get("/company", response_model=CompanyResponse)
def current_company(context: AuthorizedCompanyContext = Depends(require_authorized_company_context)) -> CompanyResponse:
    return company_response(context)


@router.put("/company", response_model=CompanyResponse)
def update_current_company(
    payload: CompanyUpdateRequest,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> CompanyResponse:
    organization_service.update_company(context.company, payload)
    database.commit()
    database.refresh(context.company)
    return company_response(context)


@router.get("/branches", response_model=list[BranchResponse])
def list_branches(
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> list[BranchResponse]:
    return [branch_response(branch) for branch in organization_service.branches_for_company(database, context.company.id)]


@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(
    payload: BranchInput,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> BranchResponse:
    branch = organization_service.create_branch(context.company, payload)
    database.add(branch)
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise conflict() from error
    database.refresh(branch)
    return branch_response(branch)


@router.get("/branches/{branch_id}", response_model=BranchResponse)
def get_branch(
    branch_id: UUID,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> BranchResponse:
    branch = organization_service.branch_for_company(database, context.company.id, branch_id)
    if branch is None:
        raise not_found()
    return branch_response(branch)


@router.put("/branches/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: UUID,
    payload: BranchInput,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> BranchResponse:
    branch = organization_service.branch_for_company(database, context.company.id, branch_id)
    if branch is None:
        raise not_found()
    organization_service.update_branch(branch, payload)
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise conflict() from error
    database.refresh(branch)
    return branch_response(branch)


@router.patch("/branches/{branch_id}/status", response_model=BranchResponse)
def set_branch_status(
    branch_id: UUID,
    payload: ActiveStatusRequest,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> BranchResponse:
    branch = organization_service.branch_for_company(database, context.company.id, branch_id)
    if branch is None:
        raise not_found()
    branch.is_active = payload.is_active
    database.commit()
    database.refresh(branch)
    return branch_response(branch)


@router.get("/warehouses", response_model=list[WarehouseResponse])
def list_warehouses(
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> list[WarehouseResponse]:
    return [warehouse_response(item) for item in organization_service.warehouses_for_company(database, context.company.id)]


@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseInput,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> WarehouseResponse:
    try:
        warehouse = organization_service.create_warehouse(database, context.company, payload)
        database.commit()
    except ValueError as error:
        database.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except IntegrityError as error:
        database.rollback()
        raise conflict() from error
    database.refresh(warehouse)
    return warehouse_response(warehouse)


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(
    warehouse_id: UUID,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> WarehouseResponse:
    warehouse = organization_service.warehouse_for_company(database, context.company.id, warehouse_id)
    if warehouse is None:
        raise not_found()
    return warehouse_response(warehouse)


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: UUID,
    payload: WarehouseInput,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> WarehouseResponse:
    warehouse = organization_service.warehouse_for_company(database, context.company.id, warehouse_id)
    if warehouse is None:
        raise not_found()
    try:
        organization_service.update_warehouse(database, warehouse, payload)
        database.commit()
    except ValueError as error:
        database.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except IntegrityError as error:
        database.rollback()
        raise conflict() from error
    database.refresh(warehouse)
    return warehouse_response(warehouse)


@router.patch("/warehouses/{warehouse_id}/status", response_model=WarehouseResponse)
def set_warehouse_status(
    warehouse_id: UUID,
    payload: ActiveStatusRequest,
    context: AuthorizedCompanyContext = Depends(require_authorized_company_context),
    database: DatabaseSession = Depends(get_db),
) -> WarehouseResponse:
    warehouse = organization_service.warehouse_for_company(database, context.company.id, warehouse_id)
    if warehouse is None:
        raise not_found()
    warehouse.is_active = payload.is_active
    database.commit()
    database.refresh(warehouse)
    return warehouse_response(warehouse)
