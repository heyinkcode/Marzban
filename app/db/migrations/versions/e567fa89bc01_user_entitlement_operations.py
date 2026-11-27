"""Store native entitlement receipts without changing existing users.

Revision ID: e567fa89bc01
Revises: d456ef78ab90
"""
from alembic import op
import sqlalchemy as sa

revision = "e567fa89bc01"
down_revision = "d456ef78ab90"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_entitlement_operations",
        sa.Column("operation_id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(34), nullable=False),
        sa.Column("user_created_at", sa.DateTime(), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("reset_id", sa.Integer()),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("receipt", sa.JSON(), nullable=False),
    )
    op.create_index("ix_user_entitlement_operations_user_id", "user_entitlement_operations", ["user_id"])


def downgrade():
    table = sa.table("user_entitlement_operations", sa.column("operation_id"))
    if op.get_bind().execute(sa.select(table.c.operation_id).limit(1)).first() is not None:
        raise RuntimeError("Entitlement operation receipts exist; refusing to discard audit history")
    op.drop_index("ix_user_entitlement_operations_user_id", table_name="user_entitlement_operations")
    op.drop_table("user_entitlement_operations")
