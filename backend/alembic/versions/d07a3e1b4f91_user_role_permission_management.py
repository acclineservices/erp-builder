"""P007 user, role, permission, and company administration foundation.

Revision ID: d07a3e1b4f91
Revises: c83a91d4e6f2
Create Date: 2026-09-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d07a3e1b4f91"
down_revision: Union[str, Sequence[str], None] = "c83a91d4e6f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("roles", sa.Column("company_id", sa.Uuid(), nullable=True))
    op.add_column("roles", sa.Column("is_system_managed", sa.Boolean(), nullable=False, server_default="false"))
    with op.batch_alter_table("roles") as batch_op:
        batch_op.drop_constraint("role_scope_name", type_="unique")
        batch_op.create_foreign_key("role_company", "companies", ["company_id"], ["id"], ondelete="CASCADE")
        batch_op.create_unique_constraint("company_role_name", ["company_id", "name"])
        batch_op.create_index("ix_roles_company_id", ["company_id"], unique=False)

    op.add_column("user_company_accesses", sa.Column("default_branch_id", sa.Uuid(), nullable=True))
    op.add_column("user_company_accesses", sa.Column("default_warehouse_id", sa.Uuid(), nullable=True))
    with op.batch_alter_table("user_company_accesses") as batch_op:
        batch_op.create_foreign_key("user_access_default_branch", "branches", ["default_branch_id"], ["id"], ondelete="RESTRICT")
        batch_op.create_foreign_key("user_access_default_warehouse", "warehouses", ["default_warehouse_id"], ["id"], ondelete="RESTRICT")
        batch_op.create_index("ix_user_company_accesses_default_branch_id", ["default_branch_id"], unique=False)
        batch_op.create_index("ix_user_company_accesses_default_warehouse_id", ["default_warehouse_id"], unique=False)

    op.create_table(
        "user_management_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("target_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_management_audit_events_company_id", "user_management_audit_events", ["company_id"], unique=False)
    op.create_index("ix_user_management_audit_events_actor_user_id", "user_management_audit_events", ["actor_user_id"], unique=False)
    op.create_index("ix_user_management_audit_events_target_user_id", "user_management_audit_events", ["target_user_id"], unique=False)
    op.create_index("ix_user_management_audit_events_action", "user_management_audit_events", ["action"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_management_audit_events_action", table_name="user_management_audit_events")
    op.drop_index("ix_user_management_audit_events_target_user_id", table_name="user_management_audit_events")
    op.drop_index("ix_user_management_audit_events_actor_user_id", table_name="user_management_audit_events")
    op.drop_index("ix_user_management_audit_events_company_id", table_name="user_management_audit_events")
    op.drop_table("user_management_audit_events")
    with op.batch_alter_table("user_company_accesses") as batch_op:
        batch_op.drop_index("ix_user_company_accesses_default_warehouse_id")
        batch_op.drop_index("ix_user_company_accesses_default_branch_id")
        batch_op.drop_constraint("user_access_default_warehouse", type_="foreignkey")
        batch_op.drop_constraint("user_access_default_branch", type_="foreignkey")
    op.drop_column("user_company_accesses", "default_warehouse_id")
    op.drop_column("user_company_accesses", "default_branch_id")
    with op.batch_alter_table("roles") as batch_op:
        batch_op.drop_index("ix_roles_company_id")
        batch_op.drop_constraint("company_role_name", type_="unique")
        batch_op.drop_constraint("role_company", type_="foreignkey")
        batch_op.create_unique_constraint("role_scope_name", ["scope", "name"])
    op.drop_column("roles", "is_system_managed")
    op.drop_column("roles", "company_id")
