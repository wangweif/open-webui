"""Add oauth_server tables

Revision ID: c8d9e0f1a2b3
Revises: b3c4d5e6f7a8
Create Date: 2026-07-21 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from open_webui.migrations.util import get_existing_tables


revision = "c8d9e0f1a2b3"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade():
    existing_tables = set(get_existing_tables())

    if "oauth_client" not in existing_tables:
        op.create_table(
            "oauth_client",
            sa.Column("client_id", sa.String(255), primary_key=True),
            sa.Column("client_secret", sa.Text(), nullable=False),
            sa.Column("client_name", sa.String(255), nullable=False),
            sa.Column("redirect_uris", sa.Text(), nullable=False),
            sa.Column("grant_types", sa.String(255), nullable=False, server_default="authorization_code,refresh_token"),
            sa.Column("scope", sa.String(255), nullable=False, server_default="openid profile"),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=False),
        )

    if "oauth_code" not in existing_tables:
        op.create_table(
            "oauth_code",
            sa.Column("code", sa.String(255), primary_key=True),
            sa.Column("client_id", sa.String(255), nullable=False),
            sa.Column("user_id", sa.String(255), nullable=False),
            sa.Column("redirect_uri", sa.Text(), nullable=False),
            sa.Column("scope", sa.String(255), nullable=False),
            sa.Column("state", sa.String(255), nullable=True),
            sa.Column("expires_at", sa.BigInteger(), nullable=False),
            sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    if "oauth_refresh_token" not in existing_tables:
        op.create_table(
            "oauth_refresh_token",
            sa.Column("token", sa.String(255), primary_key=True),
            sa.Column("client_id", sa.String(255), nullable=False),
            sa.Column("user_id", sa.String(255), nullable=False),
            sa.Column("scope", sa.String(255), nullable=False),
            sa.Column("expires_at", sa.BigInteger(), nullable=False),
            sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = set(get_existing_tables())

    for table in ["oauth_refresh_token", "oauth_code", "oauth_client"]:
        if table in existing:
            op.drop_table(table)
