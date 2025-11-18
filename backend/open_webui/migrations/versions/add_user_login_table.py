"""Add user_login table

Revision ID: f1a2b3c4d5e6
Revises: e2f3a4b5c6d7
Create Date: 2025-01-18 10:40:00.000000

"""

from alembic import op
import sqlalchemy as sa
from open_webui.migrations.util import get_existing_tables

revision = "f1a2b3c4d5e6"
down_revision = "e2f3a4b5c6d7"  # 基于最新的user fields迁移
branch_labels = None
depends_on = None


def upgrade():
    existing_tables = set(get_existing_tables())
    
    # Create user_login table if it doesn't exist
    if "user_login" not in existing_tables:
        op.create_table(
            "user_login",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("ip_address", sa.String(45), nullable=False),  # 支持IPv6
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("login_method", sa.String(50), nullable=True),  # 'password', 'ldap', 'oauth', 'trusted_header'
            sa.Column("success", sa.String(10), default='true'),  # 'true' or 'false'
            sa.Column("created_at", sa.BigInteger(), nullable=False),
        )
        
        # Create indexes
        op.create_index('idx_user_login_user_id', 'user_login', ['user_id'])
        op.create_index('idx_user_login_created_at', 'user_login', ['created_at'])
        op.create_index('idx_user_login_user_id_created_at', 'user_login', ['user_id', 'created_at'])


def downgrade():
    # Drop user_login table
    op.drop_index('idx_user_login_user_id_created_at', table_name='user_login')
    op.drop_index('idx_user_login_created_at', table_name='user_login')
    op.drop_index('idx_user_login_user_id', table_name='user_login')
    op.drop_table("user_login")

