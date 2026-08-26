"""Add permitted claims to guardrails.

Revision ID: 0021_guardrail_permitted_claims
Revises: 0020_google_drive_connections
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0021_guardrail_permitted_claims"
down_revision: str | None = "0020_google_drive_connections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "guardrails",
        sa.Column(
            "permitted_claims",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.alter_column("guardrails", "permitted_claims", server_default=None)


def downgrade() -> None:
    op.drop_column("guardrails", "permitted_claims")