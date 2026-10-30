"""Dedicated Node authorization; existing Nodes remain public.

Revision ID: d456ef78ab90
Revises: c345de67fa89
"""
from alembic import op
import sqlalchemy as sa

revision = "d456ef78ab90"
down_revision = "c345de67fa89"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("nodes", sa.Column("access_mode", sa.String(16), nullable=False, server_default="public"))
    op.add_column("nodes", sa.Column("access_revision", sa.Integer(), nullable=False, server_default="0"))
    with op.batch_alter_table("hosts") as batch:
        batch.add_column(sa.Column("node_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_hosts_node", "nodes", ["node_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_hosts_node_id", ["node_id"])
    for name, columns in (
        ("dedicated_node_grants", [
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("username", sa.String(34), nullable=False),
            sa.Column("user_created_at", sa.DateTime(), nullable=False),
            sa.Column("granted_by", sa.String(34), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        ]),
        ("dedicated_node_admins", [
            sa.Column("admin_id", sa.Integer(), sa.ForeignKey("admins.id", ondelete="CASCADE"), primary_key=True),
        ]),
    ):
        op.create_table(name, sa.Column("node_id", sa.Integer(), sa.ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True), *columns)
    op.create_table("dedicated_node_operations",
        sa.Column("operation_id", sa.String(36), primary_key=True),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(34), nullable=False),
        sa.Column("user_created_at", sa.DateTime(), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("actor", sa.String(34), nullable=False),
        sa.Column("external_reference", sa.String(128), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    # Bind only unambiguous, exact legacy endpoints; never guess aliases or DNS.
    conn = op.get_bind()
    nodes = conn.execute(sa.text("SELECT id, address FROM nodes")).fetchall()
    by_address = {}
    for node_id, address in nodes:
        by_address.setdefault(address.strip().lower(), []).append(node_id)
    for host_id, address in conn.execute(sa.text("SELECT id, address FROM hosts")).fetchall():
        ids = by_address.get(address.strip().lower(), [])
        if len(ids) == 1:
            conn.execute(sa.text("UPDATE hosts SET node_id=:node WHERE id=:host"), {"node": ids[0], "host": host_id})


def downgrade():
    conn = op.get_bind()
    if (conn.execute(sa.text("SELECT COUNT(*) FROM nodes WHERE access_mode <> 'public'")).scalar()
            or conn.execute(sa.text("SELECT COUNT(*) FROM dedicated_node_operations")).scalar()):
        raise RuntimeError("Dedicated access/audit exists: keep the new runtime; downgrade would expose Nodes")
    for name in ("dedicated_node_operations", "dedicated_node_admins", "dedicated_node_grants"):
        op.drop_table(name)
    with op.batch_alter_table("hosts") as batch:
        batch.drop_index("ix_hosts_node_id")
        batch.drop_constraint("fk_hosts_node", type_="foreignkey")
        batch.drop_column("node_id")
    op.drop_column("nodes", "access_revision")
    op.drop_column("nodes", "access_mode")
