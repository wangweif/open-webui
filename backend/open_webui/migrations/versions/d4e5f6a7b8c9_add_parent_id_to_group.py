"""Add parent_id to group table

Revision ID: d4e5f6a7b8c9
Revises: c8d9e0f1a2b3
Create Date: 2026-07-31 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from open_webui.migrations.util import get_existing_tables


revision = "d4e5f6a7b8c9"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade():
    existing_tables = set(get_existing_tables())

    if "group" not in existing_tables:
        return

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("group")}

    if "parent_id" not in columns:
        op.add_column(
            "group",
            sa.Column("parent_id", sa.Text(), nullable=True),
        )


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("group")}

    if "parent_id" in columns:
        op.drop_column("group", "parent_id")
