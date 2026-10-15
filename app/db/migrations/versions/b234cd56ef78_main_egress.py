"""Optional independent main-core outbound; existing settings are untouched."""
from alembic import op
import sqlalchemy as sa

revision = "b234cd56ef78"
down_revision = "a123bc45de67"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("main_egress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("protocol", sa.String(8), nullable=False),
        sa.Column("udp_mode", sa.String(16), nullable=False, server_default="legacy"),
        sa.Column("server", sa.String(253), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(256), nullable=True),
        sa.Column("encrypted_password", sa.String(1024), nullable=True),
        sa.CheckConstraint("id = 1", name="ck_main_egress_singleton"))


def downgrade():
    op.drop_table("main_egress")
