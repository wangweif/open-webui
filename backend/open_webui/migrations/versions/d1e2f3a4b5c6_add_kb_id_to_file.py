"""Add kb_id to file table

Revision ID: d1e2f3a4b5c6
Revises: 3781e22d8b01
Create Date: 2025-10-29 07:30:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "d1e2f3a4b5c6"
down_revision = "3781e22d8b01"
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists to avoid errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('file')]
    
    if 'kb_id' not in columns:
        print("Adding kb_id column to file table")
        op.add_column(
            "file",
            sa.Column("kb_id", sa.Text(), nullable=True),
        )
    else:
        print("kb_id column already exists in file table, skipping")


def downgrade():
    op.drop_column("file", "kb_id")

