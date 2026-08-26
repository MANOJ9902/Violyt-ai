"""Add user-scoped Google Drive OAuth connections.

Revision ID: 0020_google_drive_connections
Revises: 0019_brand_space_tagline
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0020_google_drive_connections"
down_revision: str = "0019_brand_space_tagline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "google_drive_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column(
            "scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("is_connected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["brand_space_id"], ["brand_spaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "brand_space_id", "user_id", name="uq_google_drive_connection_scope"),
    )
    op.create_index("ix_google_drive_connections_tenant_id", "google_drive_connections", ["tenant_id"])
    op.create_index("ix_google_drive_connections_brand_space_id", "google_drive_connections", ["brand_space_id"])
    op.create_index("ix_google_drive_connections_user_id", "google_drive_connections", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_google_drive_connections_user_id", table_name="google_drive_connections")
    op.drop_index("ix_google_drive_connections_brand_space_id", table_name="google_drive_connections")
    op.drop_index("ix_google_drive_connections_tenant_id", table_name="google_drive_connections")
    op.drop_table("google_drive_connections")
