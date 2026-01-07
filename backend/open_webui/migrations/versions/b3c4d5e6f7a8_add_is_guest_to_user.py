"""Add is_guest to user table

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-01-07 10:40:00.000000

"""

from alembic import op
import sqlalchemy as sa
from open_webui.migrations.util import get_existing_tables


revision = "b3c4d5e6f7a8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    existing_tables = set(get_existing_tables())

    if "user" not in existing_tables:
        return

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("user")}

    if "is_guest" not in columns:
        op.add_column(
            "user",
            sa.Column("is_guest", sa.Boolean(), nullable=True, server_default=sa.false()),
        )

    # Ensure existing rows are marked as non-guest
    op.execute(sa.text("UPDATE user SET is_guest = 0 WHERE is_guest IS NULL"))


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("user")}

    if "is_guest" in columns:
        op.drop_column("user", "is_guest")
