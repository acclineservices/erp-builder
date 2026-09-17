"""P009 product and item master management.

Revision ID: f009a1b2c3d4
Revises: e008a1b2c3d4
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f009a1b2c3d4"
down_revision = "e008a1b2c3d4"
branch_labels = None
depends_on = None

def upgrade() -> None:
    uid=postgresql.UUID(as_uuid=True)
    op.create_table("item_categories",sa.Column("id",uid,primary_key=True),sa.Column("company_id",uid,sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("name",sa.String(255),nullable=False),sa.Column("code",sa.String(64)),sa.Column("description",sa.Text()),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.text("true")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("CURRENT_TIMESTAMP")),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("CURRENT_TIMESTAMP")),sa.UniqueConstraint("company_id","name",name="item_category_company_name"))
    op.create_index("ix_item_categories_company_id","item_categories",["company_id"]); op.create_index("uq_item_category_code","item_categories",["company_id","code"],unique=True,postgresql_where=sa.text("code IS NOT NULL"))
    op.create_table("item_code_sequences",sa.Column("id",uid,primary_key=True),sa.Column("company_id",uid,sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("next_value",sa.Integer(),nullable=False,server_default="1"),sa.UniqueConstraint("company_id",name="item_code_sequence_company")); op.create_index("ix_item_code_sequences_company_id","item_code_sequences",["company_id"])
    op.create_table("items",sa.Column("id",uid,primary_key=True),sa.Column("company_id",uid,sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("category_id",uid,sa.ForeignKey("item_categories.id",ondelete="RESTRICT")),sa.Column("default_warehouse_id",uid,sa.ForeignKey("warehouses.id",ondelete="RESTRICT")),sa.Column("name",sa.String(255),nullable=False),sa.Column("display_name",sa.String(255)),sa.Column("code",sa.String(64),nullable=False),sa.Column("item_type",sa.String(16),nullable=False),sa.Column("description",sa.Text()),sa.Column("uom_code",sa.String(16),nullable=False,server_default="PCS"),sa.Column("hsn_sac_code",sa.String(16)),sa.Column("barcode",sa.String(128)),sa.Column("purchase_price",sa.Numeric(14,2)),sa.Column("selling_price",sa.Numeric(14,2)),sa.Column("gst_rate",sa.Numeric(5,2)),sa.Column("track_inventory",sa.Boolean(),nullable=False,server_default=sa.text("false")),sa.Column("opening_stock",sa.Numeric(14,3),nullable=False,server_default="0"),sa.Column("reorder_level",sa.Numeric(14,3)),sa.Column("image_url",sa.String(1024)),sa.Column("notes",sa.Text()),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.text("true")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("CURRENT_TIMESTAMP")),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("CURRENT_TIMESTAMP")),sa.CheckConstraint("item_type IN ('goods', 'service')",name="item_type"),sa.CheckConstraint("purchase_price IS NULL OR purchase_price >= 0",name="item_purchase_price"),sa.CheckConstraint("selling_price IS NULL OR selling_price >= 0",name="item_selling_price"),sa.CheckConstraint("opening_stock >= 0",name="item_opening_stock"),sa.CheckConstraint("reorder_level IS NULL OR reorder_level >= 0",name="item_reorder_level"))
    op.create_index("ix_items_company_id","items",["company_id"]); op.create_index("ix_items_category_id","items",["category_id"]); op.create_index("ix_items_default_warehouse_id","items",["default_warehouse_id"]); op.create_index("ix_items_name","items",["name"]); op.create_index("uq_item_code","items",["company_id","code"],unique=True); op.create_index("uq_item_barcode","items",["company_id","barcode"],unique=True,postgresql_where=sa.text("barcode IS NOT NULL"))
def downgrade() -> None:
    op.drop_table("items"); op.drop_table("item_code_sequences"); op.drop_table("item_categories")
