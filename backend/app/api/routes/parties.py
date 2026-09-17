"""Customer and supplier views over the shared P008 business-party model."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DatabaseSession

from app.api.dependencies import AuthorizedCompanyContext, require_authorized_company_context
from app.db.session import get_db
from app.models import Party
from app.schemas.parties import ActiveStatusRequest, PartyInput, PartyResponse
from app.services import administration as administration_service
from app.services import parties as service

router = APIRouter(prefix="/parties", tags=["business parties"])


def require(context: AuthorizedCompanyContext, database: DatabaseSession, role: str, operation: str) -> None:
    try:
        administration_service.require_permission(database, context.user, context.company, f"{role}s.{operation}")
    except administration_service.AdministrationForbidden as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this company action.") from error


def response(party: Party, role: str) -> PartyResponse:
    contact = next((item for item in party.contacts if item.contact_type == "primary"), None)
    address = next((item for item in party.addresses if item.address_type == "primary"), None)
    return PartyResponse(
        id=party.id, display_name=party.display_name, legal_name=party.legal_name,
        code=party.customer_code if role == "customer" else party.supplier_code,
        customer_code=party.customer_code, supplier_code=party.supplier_code, party_type=party.party_type,
        contact_person=contact.contact_person if contact else None, mobile_number=contact.mobile_number if contact else None,
        alternate_mobile=contact.alternate_mobile if contact else None, email=contact.email if contact else None,
        address_line1=address.address_line1 if address else None, address_line2=address.address_line2 if address else None,
        city=address.city if address else None, state=address.state if address else None,
        postal_code=address.postal_code if address else None, country=address.country if address else None,
        gst_status=party.gst_status, gstin=party.gstin, pan=party.pan, opening_balance=party.opening_balance,
        opening_balance_type=party.opening_balance_type, credit_limit=party.credit_limit,
        payment_terms_days=party.payment_terms_days, notes=party.notes, is_active=party.is_active,
    )


def conflict(error: IntegrityError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A customer or supplier with that code or GSTIN already exists in this company.")


def routes_for(role: str) -> None:
    plural = f"/{role}s"

    @router.get(plural, response_model=list[PartyResponse])
    def list_parties(
        search: str | None = None, active: bool | None = None, party_type: str | None = Query(default=None, pattern="^(customer|supplier|both)$"),
        context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
    ) -> list[PartyResponse]:
        require(context, database, role, "view")
        return [response(item, role) for item in service.parties_for_company(database, context.company.id, role, search, active, party_type)]

    @router.get(f"{plural}/{{party_id}}", response_model=PartyResponse)
    def get_party(
        party_id: UUID, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
    ) -> PartyResponse:
        require(context, database, role, "view")
        party = service.party_for_company(database, context.company.id, party_id, role)
        if party is None: raise HTTPException(status_code=404, detail="The requested party is not available in this company.")
        return response(party, role)

    @router.post(plural, response_model=PartyResponse, status_code=status.HTTP_201_CREATED)
    def create_party(
        payload: PartyInput, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
    ) -> PartyResponse:
        require(context, database, role, "create")
        try:
            party = service.create_party(database, context.company, context.user, role, payload); database.commit(); database.refresh(party)
        except service.PartyError as error:
            database.rollback(); raise HTTPException(status_code=422, detail=str(error)) from error
        except IntegrityError as error:
            database.rollback(); raise conflict(error) from error
        return response(party, role)

    @router.put(f"{plural}/{{party_id}}", response_model=PartyResponse)
    def update_party(
        party_id: UUID, payload: PartyInput, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
    ) -> PartyResponse:
        require(context, database, role, "edit")
        party = service.party_for_company(database, context.company.id, party_id, role)
        if party is None: raise HTTPException(status_code=404, detail="The requested party is not available in this company.")
        try:
            party = service.update_party(database, context.company, context.user, role, party, payload); database.commit(); database.refresh(party)
        except service.PartyError as error:
            database.rollback(); raise HTTPException(status_code=422, detail=str(error)) from error
        except IntegrityError as error:
            database.rollback(); raise conflict(error) from error
        return response(party, role)

    @router.patch(f"{plural}/{{party_id}}/status", response_model=PartyResponse)
    def set_party_status(
        party_id: UUID, payload: ActiveStatusRequest, context: AuthorizedCompanyContext = Depends(require_authorized_company_context), database: DatabaseSession = Depends(get_db),
    ) -> PartyResponse:
        require(context, database, role, "deactivate")
        party = service.party_for_company(database, context.company.id, party_id, role)
        if party is None: raise HTTPException(status_code=404, detail="The requested party is not available in this company.")
        service.set_party_status(database, context.company, context.user, role, party, payload.is_active); database.commit(); database.refresh(party)
        return response(party, role)


routes_for("customer")
routes_for("supplier")
