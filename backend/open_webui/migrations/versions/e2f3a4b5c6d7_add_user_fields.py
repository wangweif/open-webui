"""Add assistant_id, ragflow_user_id, team_id, tenant_id to user table

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2025-10-29 07:35:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    # Check existing columns to avoid errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user')]
    
    # Add assistant_id column if not exists
    if 'assistant_id' not in columns:
        print("Adding assistant_id column to user table")
        op.add_column(
            "user",
            sa.Column("assistant_id", sa.String(), nullable=True),
        )
    else:
        print("assistant_id column already exists in user table, skipping")
    
    # Add ragflow_user_id column if not exists
    if 'ragflow_user_id' not in columns:
        print("Adding ragflow_user_id column to user table")
        op.add_column(
            "user",
            sa.Column("ragflow_user_id", sa.String(), nullable=True),
        )
    else:
        print("ragflow_user_id column already exists in user table, skipping")
    
    # Add team_id column if not exists
    if 'team_id' not in columns:
        print("Adding team_id column to user table")
        op.add_column(
            "user",
            sa.Column("team_id", sa.String(), nullable=True),
        )
    else:
        print("team_id column already exists in user table, skipping")
    
    # Add tenant_id column if not exists
    if 'tenant_id' not in columns:
        print("Adding tenant_id column to user table")
        op.add_column(
            "user",
            sa.Column("tenant_id", sa.String(), nullable=True),
        )
    else:
        print("tenant_id column already exists in user table, skipping")


def downgrade():
    op.drop_column("user", "tenant_id")
    op.drop_column("user", "team_id")
    op.drop_column("user", "ragflow_user_id")
    op.drop_column("user", "assistant_id")

