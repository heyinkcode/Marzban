"""Add audited usage continuity receipts without rewriting user/history data."""
from alembic import op
import sqlalchemy as sa

revision = "c345de67fa89"
down_revision = "b234cd56ef78"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("user_usage_recoveries",
        sa.Column("operation_id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(34), nullable=False),
        sa.Column("user_created_at", sa.DateTime(), nullable=False),
        sa.Column("reset_id", sa.Integer(), nullable=False),
        sa.Column("restored_bytes", sa.BigInteger(), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("receipt", sa.JSON(), nullable=False),
        sa.UniqueConstraint("user_id", "user_created_at", "username", "reset_id", name="uq_usage_recovery_target"),
        sa.CheckConstraint("restored_bytes > 0", name="ck_usage_recovery_positive"))
    op.create_index("ix_user_usage_recoveries_user_id", "user_usage_recoveries", ["user_id"])


def downgrade():
    # Removing applied corrections would silently double-charge lifetime usage.
    if op.get_bind().execute(sa.text("SELECT count(*) FROM user_usage_recoveries")).scalar():
        raise RuntimeError("Applied usage recoveries exist: downgrade requires an audited data migration")
    op.drop_index("ix_user_usage_recoveries_user_id", table_name="user_usage_recoveries")
    op.drop_table("user_usage_recoveries")
