"""P008 customer and supplier master-data foundation.

Revision ID: e008a1b2c3d4
Revises: d07a3e1b4f91
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e008a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d07a3e1b4f91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "parties",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("party_type", sa.String(length=16), nullable=False), sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True), sa.Column("customer_code", sa.String(length=64), nullable=True), sa.Column("supplier_code", sa.String(length=64), nullable=True),
        sa.Column("gst_status", sa.String(length=32), nullable=False, server_default="unregistered"), sa.Column("gstin", sa.String(length=32), nullable=True), sa.Column("pan", sa.String(length=16), nullable=True),
        sa.Column("opening_balance", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"), sa.Column("opening_balance_type", sa.String(length=8), nullable=False, server_default="debit"),
        sa.Column("credit_limit", sa.Numeric(precision=14, scale=2), nullable=True), sa.Column("payment_terms_days", sa.Integer(), nullable=True), sa.Column("notes", sa.Text(), nullable=True), sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("party_type IN ('customer', 'supplier', 'both')", name="party_type"), sa.CheckConstraint("customer_code IS NOT NULL OR supplier_code IS NOT NULL", name="party_has_role"), sa.CheckConstraint("gst_status IN ('registered', 'unregistered', 'composition', 'exempt')", name="party_gst_status"), sa.CheckConstraint("opening_balance >= 0", name="party_opening_balance"), sa.CheckConstraint("opening_balance_type IN ('debit', 'credit')", name="party_opening_balance_type"), sa.CheckConstraint("credit_limit IS NULL OR credit_limit >= 0", name="party_credit_limit"), sa.CheckConstraint("payment_terms_days IS NULL OR payment_terms_days >= 0", name="party_payment_terms"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parties_company_id", "parties", ["company_id"]); op.create_index("ix_parties_display_name", "parties", ["display_name"])
    op.create_index("uq_party_customer_code", "parties", ["company_id", "customer_code"], unique=True, postgresql_where=sa.text("customer_code IS NOT NULL"))
    op.create_index("uq_party_supplier_code", "parties", ["company_id", "supplier_code"], unique=True, postgresql_where=sa.text("supplier_code IS NOT NULL"))
    op.create_index("uq_party_gstin", "parties", ["company_id", "gstin"], unique=True, postgresql_where=sa.text("gstin IS NOT NULL"))
    op.create_table("party_contacts", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("party_id", sa.Uuid(), nullable=False), sa.Column("contact_type", sa.String(length=32), nullable=False, server_default="primary"), sa.Column("contact_person", sa.String(length=255), nullable=True), sa.Column("mobile_number", sa.String(length=32), nullable=True), sa.Column("alternate_mobile", sa.String(length=32), nullable=True), sa.Column("email", sa.String(length=320), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False), sa.ForeignKeyConstraint(["party_id"], ["parties.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("party_id", "contact_type", name="party_contact_type"))
    op.create_index("ix_party_contacts_party_id", "party_contacts", ["party_id"])
    op.create_table("party_addresses", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("party_id", sa.Uuid(), nullable=False), sa.Column("address_type", sa.String(length=32), nullable=False, server_default="primary"), sa.Column("address_line1", sa.String(length=255), nullable=True), sa.Column("address_line2", sa.String(length=255), nullable=True), sa.Column("city", sa.String(length=128), nullable=True), sa.Column("state", sa.String(length=128), nullable=True), sa.Column("postal_code", sa.String(length=32), nullable=True), sa.Column("country", sa.String(length=128), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False), sa.ForeignKeyConstraint(["party_id"], ["parties.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("party_id", "address_type", name="party_address_type"))
    op.create_index("ix_party_addresses_party_id", "party_addresses", ["party_id"])
    op.create_table("party_code_sequences", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("company_id", sa.Uuid(), nullable=False), sa.Column("sequence_type", sa.String(length=16), nullable=False), sa.Column("next_value", sa.Integer(), nullable=False, server_default="1"), sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("company_id", "sequence_type", name="party_code_sequence_company_type"))
    op.create_index("ix_party_code_sequences_company_id", "party_code_sequences", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_party_code_sequences_company_id", table_name="party_code_sequences"); op.drop_table("party_code_sequences")
    op.drop_index("ix_party_addresses_party_id", table_name="party_addresses"); op.drop_table("party_addresses")
    op.drop_index("ix_party_contacts_party_id", table_name="party_contacts"); op.drop_table("party_contacts")
    op.drop_index("uq_party_gstin", table_name="parties"); op.drop_index("uq_party_supplier_code", table_name="parties"); op.drop_index("uq_party_customer_code", table_name="parties")
    op.drop_index("ix_parties_display_name", table_name="parties"); op.drop_index("ix_parties_company_id", table_name="parties"); op.drop_table("parties")
