"""Add explicitly managed subscription periods without updating any user.

Revision ID: f678ab90cd12
Revises: e567fa89bc01
"""
from alembic import op
import sqlalchemy as sa

revision = "f678ab90cd12"
down_revision = "e567fa89bc01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_subscription_periods",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("username", sa.String(34), nullable=False),
        sa.Column("user_created_at", sa.DateTime, nullable=False),
        sa.Column("period_id", sa.String(36), nullable=False),
        sa.Column("starts_at", sa.BigInteger, nullable=False),
        sa.Column("base_quota_bytes", sa.BigInteger, nullable=False),
        sa.UniqueConstraint("user_id", "user_created_at", "period_id", name="uq_user_subscription_period"),
        sa.CheckConstraint("base_quota_bytes > 0 AND starts_at > 0", name="ck_user_subscription_period_terms"),
    )


def downgrade():
    table = sa.table("user_subscription_periods", sa.column("id"))
    if op.get_bind().execute(sa.select(table.c.id).limit(1)).first() is not None:
        raise RuntimeError("Managed subscription periods exist; refusing to discard their identities")
    op.drop_table("user_subscription_periods")
