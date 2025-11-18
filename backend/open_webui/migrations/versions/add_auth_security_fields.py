"""Add security fields to auth table

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2025-01-20 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from open_webui.migrations.util import get_existing_tables

revision = "a1b2c3d4e5f6"
down_revision = "f1a2b3c4d5e6"  # 基于user_login迁移
branch_labels = None
depends_on = None


def upgrade():
    existing_tables = set(get_existing_tables())
    
    # Add security fields to auth table if it exists
    if "auth" in existing_tables:
        # Check if columns already exist before adding
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_columns = {col['name'] for col in inspector.get_columns('auth')}
        
        if 'password_changed_at' not in existing_columns:
            op.add_column('auth', sa.Column('password_changed_at', sa.BigInteger(), nullable=True))
        
        if 'failed_login_count' not in existing_columns:
            op.add_column('auth', sa.Column('failed_login_count', sa.Integer(), nullable=True, server_default='0'))
        
        if 'locked_until' not in existing_columns:
            op.add_column('auth', sa.Column('locked_until', sa.BigInteger(), nullable=True))
        
        # Update existing records: set password_changed_at to current time if null
        # This ensures existing users don't have expired passwords immediately
        import time
        current_time = int(time.time())
        op.execute(
            sa.text(f"UPDATE auth SET password_changed_at = {current_time} WHERE password_changed_at IS NULL")
        )
        
        # Set default failed_login_count to 0 for existing records
        op.execute(
            sa.text("UPDATE auth SET failed_login_count = 0 WHERE failed_login_count IS NULL")
        )


def downgrade():
    # Remove security fields from auth table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {col['name'] for col in inspector.get_columns('auth')}
    
    if 'locked_until' in existing_columns:
        op.drop_column('auth', 'locked_until')
    
    if 'failed_login_count' in existing_columns:
        op.drop_column('auth', 'failed_login_count')
    
    if 'password_changed_at' in existing_columns:
        op.drop_column('auth', 'password_changed_at')

