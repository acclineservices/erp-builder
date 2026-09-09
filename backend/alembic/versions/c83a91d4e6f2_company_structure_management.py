"""P006 company, branch, and warehouse management.

Revision ID: c83a91d4e6f2
Revises: b71f4e9c2a10
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c83a91d4e6f2"
down_revision: Union[str, Sequence[str], None] = "b71f4e9c2a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional company profile and operating-location fields without changing existing records."""
    op.add_column("companies", sa.Column("legal_name", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("display_name", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("business_type", sa.String(length=64), nullable=False, server_default="proprietorship"))
    op.add_column("companies", sa.Column("status", sa.String(length=16), nullable=False, server_default="active"))
    op.add_column("companies", sa.Column("gst_status", sa.String(length=32), nullable=True))
    op.add_column("companies", sa.Column("gstin", sa.String(length=32), nullable=True))
    op.add_column("companies", sa.Column("email", sa.String(length=320), nullable=True))
    op.add_column("companies", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column("companies", sa.Column("address_line1", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("address_line2", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("city", sa.String(length=128), nullable=True))
    op.add_column("companies", sa.Column("state", sa.String(length=128), nullable=True))
    op.add_column("companies", sa.Column("postal_code", sa.String(length=32), nullable=True))
    op.add_column("companies", sa.Column("country", sa.String(length=128), nullable=True))
    op.add_column("companies", sa.Column("logo_url", sa.String(length=1024), nullable=True))
    with op.batch_alter_table("companies") as batch_op:
        batch_op.create_check_constraint("company_status", "status IN ('active', 'suspended', 'closed')")

    for table in ("branches",):
        op.add_column(table, sa.Column("code", sa.String(length=64), nullable=True))
        op.add_column(table, sa.Column("email", sa.String(length=320), nullable=True))
        op.add_column(table, sa.Column("phone", sa.String(length=32), nullable=True))
        op.add_column(table, sa.Column("address_line1", sa.String(length=255), nullable=True))
        op.add_column(table, sa.Column("address_line2", sa.String(length=255), nullable=True))
        op.add_column(table, sa.Column("city", sa.String(length=128), nullable=True))
        op.add_column(table, sa.Column("state", sa.String(length=128), nullable=True))
        op.add_column(table, sa.Column("postal_code", sa.String(length=32), nullable=True))
        op.add_column(table, sa.Column("country", sa.String(length=128), nullable=True))

    op.add_column("warehouses", sa.Column("code", sa.String(length=64), nullable=True))
    op.add_column("warehouses", sa.Column("branch_id", sa.Uuid(), nullable=True))
    op.add_column("warehouses", sa.Column("contact_person", sa.String(length=255), nullable=True))
    op.add_column("warehouses", sa.Column("contact_number", sa.String(length=32), nullable=True))
    op.add_column("warehouses", sa.Column("address_line1", sa.String(length=255), nullable=True))
    op.add_column("warehouses", sa.Column("address_line2", sa.String(length=255), nullable=True))
    op.add_column("warehouses", sa.Column("city", sa.String(length=128), nullable=True))
    op.add_column("warehouses", sa.Column("state", sa.String(length=128), nullable=True))
    op.add_column("warehouses", sa.Column("postal_code", sa.String(length=32), nullable=True))
    op.add_column("warehouses", sa.Column("country", sa.String(length=128), nullable=True))
    with op.batch_alter_table("warehouses") as batch_op:
        batch_op.create_foreign_key("warehouse_branch", "branches", ["branch_id"], ["id"], ondelete="RESTRICT")
        batch_op.create_index("ix_warehouses_branch_id", ["branch_id"], unique=False)


def downgrade() -> None:
    """Remove P006 additions in reverse order."""
    with op.batch_alter_table("warehouses") as batch_op:
        batch_op.drop_index("ix_warehouses_branch_id")
        batch_op.drop_constraint("warehouse_branch", type_="foreignkey")
    for column in ("country", "postal_code", "state", "city", "address_line2", "address_line1", "contact_number", "contact_person", "branch_id", "code"):
        op.drop_column("warehouses", column)

    for column in ("country", "postal_code", "state", "city", "address_line2", "address_line1", "phone", "email", "code"):
        op.drop_column("branches", column)

    with op.batch_alter_table("companies") as batch_op:
        batch_op.drop_constraint("company_status", type_="check")
    for column in ("logo_url", "country", "postal_code", "state", "city", "address_line2", "address_line1", "phone", "email", "gstin", "gst_status", "status", "business_type", "display_name", "legal_name"):
        op.drop_column("companies", column)
