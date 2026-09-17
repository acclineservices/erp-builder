"""Tenant-scoped customer and supplier master-data operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Company, Party, PartyAddress, PartyCodeSequence, PartyContact, User
from app.models.identity import UserManagementAuditEvent
from app.schemas.parties import PartyInput


class PartyError(ValueError):
    pass


def _clean(value: str | None) -> str | None:
    return value.strip() if value and value.strip() else None


def party_for_company(database: Session, company_id: UUID, party_id: UUID, role: str) -> Party | None:
    column = Party.customer_code if role == "customer" else Party.supplier_code
    return database.scalar(select(Party).where(Party.id == party_id, Party.company_id == company_id, column.is_not(None)))


def parties_for_company(database: Session, company_id: UUID, role: str, search: str | None = None, active: bool | None = None, party_type: str | None = None) -> list[Party]:
    column = Party.customer_code if role == "customer" else Party.supplier_code
    query = select(Party).where(Party.company_id == company_id, column.is_not(None))
    if active is not None:
        query = query.where(Party.is_active.is_(active))
    if party_type in {"customer", "supplier", "both"}:
        query = query.where(Party.party_type == party_type)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Party.display_name.ilike(pattern), Party.legal_name.ilike(pattern), Party.customer_code.ilike(pattern), Party.supplier_code.ilike(pattern), Party.gstin.ilike(pattern), Party.id.in_(select(PartyContact.party_id).where(or_(PartyContact.mobile_number.ilike(pattern), PartyContact.email.ilike(pattern))))))
    return list(database.scalars(query.order_by(Party.display_name, Party.created_at)).all())


def _next_code(database: Session, company_id: UUID, role: str) -> str:
    sequence = database.scalar(select(PartyCodeSequence).where(PartyCodeSequence.company_id == company_id, PartyCodeSequence.sequence_type == role).with_for_update())
    if sequence is None:
        sequence = PartyCodeSequence(company_id=company_id, sequence_type=role, next_value=1)
        database.add(sequence)
        database.flush()
    value = sequence.next_value
    sequence.next_value += 1
    return f"{'CUS' if role == 'customer' else 'SUP'}-{value:04d}"


def _primary_contact(party: Party) -> PartyContact:
    return next((item for item in party.contacts if item.contact_type == "primary"), PartyContact(party=party, contact_type="primary"))


def _primary_address(party: Party) -> PartyAddress:
    return next((item for item in party.addresses if item.address_type == "primary"), PartyAddress(party=party, address_type="primary"))


def _set_primary_foundation(database: Session, party: Party, payload: PartyInput) -> None:
    contact = _primary_contact(party)
    contact.contact_person, contact.mobile_number, contact.alternate_mobile, contact.email = payload.contact_person, payload.mobile_number, payload.alternate_mobile, payload.email
    address = _primary_address(party)
    address.address_line1, address.address_line2, address.city, address.state, address.postal_code, address.country = payload.address_line1, payload.address_line2, payload.city, payload.state, payload.postal_code, payload.country
    database.add(contact)
    database.add(address)


def _record_audit(database: Session, company_id: UUID, actor: User, action: str, party: Party) -> None:
    database.add(UserManagementAuditEvent(company_id=company_id, actor_user_id=actor.id, action=action, details=f"party:{party.id}"))


def _requested_type(payload: PartyInput, endpoint_role: str) -> str:
    if payload.party_type and payload.party_type not in {endpoint_role, "both"}:
        raise PartyError(f"Use the {payload.party_type} API to create that party type.")
    return payload.party_type or endpoint_role


def create_party(database: Session, company: Company, actor: User, endpoint_role: str, payload: PartyInput) -> Party:
    party_type = _requested_type(payload, endpoint_role)
    endpoint_code = _clean(payload.code) or _next_code(database, company.id, endpoint_role)
    customer_code = endpoint_code if endpoint_role == "customer" else (_next_code(database, company.id, "customer") if party_type == "both" else None)
    supplier_code = endpoint_code if endpoint_role == "supplier" else (_next_code(database, company.id, "supplier") if party_type == "both" else None)
    values = payload.model_dump(exclude={"code", "party_type", "contact_person", "mobile_number", "alternate_mobile", "email", "address_line1", "address_line2", "city", "state", "postal_code", "country"})
    party = Party(company=company, party_type=party_type, customer_code=customer_code, supplier_code=supplier_code, **values)
    database.add(party)
    _set_primary_foundation(database, party, payload)
    database.flush()
    _record_audit(database, company.id, actor, f"{endpoint_role}_created", party)
    return party


def update_party(database: Session, company: Company, actor: User, endpoint_role: str, party: Party, payload: PartyInput) -> Party:
    requested = _requested_type(payload, endpoint_role)
    if requested != party.party_type:
        if requested != "both":
            raise PartyError("A party role cannot be removed; keep the party as Both for audit-safe master data.")
        party.party_type = "both"
        if endpoint_role == "customer" and not party.supplier_code: party.supplier_code = _next_code(database, company.id, "supplier")
        if endpoint_role == "supplier" and not party.customer_code: party.customer_code = _next_code(database, company.id, "customer")
    for field, value in payload.model_dump(exclude={"code", "party_type", "contact_person", "mobile_number", "alternate_mobile", "email", "address_line1", "address_line2", "city", "state", "postal_code", "country"}).items():
        setattr(party, field, value)
    if payload.code:
        setattr(party, "customer_code" if endpoint_role == "customer" else "supplier_code", _clean(payload.code))
    _set_primary_foundation(database, party, payload)
    database.flush()
    _record_audit(database, company.id, actor, f"{endpoint_role}_updated", party)
    return party


def set_party_status(database: Session, company: Company, actor: User, endpoint_role: str, party: Party, is_active: bool) -> Party:
    party.is_active = is_active
    _record_audit(database, company.id, actor, f"{endpoint_role}_{'activated' if is_active else 'deactivated'}", party)
    return party
