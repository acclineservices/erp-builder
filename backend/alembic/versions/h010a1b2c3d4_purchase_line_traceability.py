"""P010 purchase source-line traceability.

Revision ID: h010a1b2c3d4
Revises: g010a1b2c3d4
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "h010a1b2c3d4"
down_revision = "g010a1b2c3d4"
branch_labels = None
depends_on = None

def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=True)
    # Batch mode keeps the full migration chain executable in SQLite tests.
    with op.batch_alter_table("purchase_invoice_lines") as batch:
        batch.add_column(sa.Column("purchase_order_line_id", uid, sa.ForeignKey("purchase_order_lines.id", ondelete="RESTRICT"), nullable=True))
        batch.add_column(sa.Column("goods_receipt_line_id", uid, sa.ForeignKey("goods_receipt_lines.id", ondelete="RESTRICT"), nullable=True))
        batch.create_index("ix_purchase_invoice_lines_purchase_order_line_id", ["purchase_order_line_id"])
        batch.create_index("ix_purchase_invoice_lines_goods_receipt_line_id", ["goods_receipt_line_id"])

def downgrade() -> None:
    with op.batch_alter_table("purchase_invoice_lines") as batch:
        batch.drop_index("ix_purchase_invoice_lines_goods_receipt_line_id")
        batch.drop_index("ix_purchase_invoice_lines_purchase_order_line_id")
        batch.drop_column("goods_receipt_line_id")
        batch.drop_column("purchase_order_line_id")
