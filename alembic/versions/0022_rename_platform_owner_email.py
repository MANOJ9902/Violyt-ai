"""Rename the existing Platform Owner email.

Revision ID: 0022_rename_platform_owner_email
Revises: 0021_guardrail_permitted_claims
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0022_rename_platform_owner_email"
down_revision: str | None = "0021_guardrail_permitted_claims"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGACY_PLATFORM_OWNER_EMAIL = "owner@violyt.ai"
PLATFORM_OWNER_EMAIL = "admin@violyt.ai"
PLATFORM_OWNER_ROLE = "super_admin"


def _rename_platform_owner_email(source_email: str, target_email: str) -> None:
    bind = op.get_bind()
    source_owner_id = bind.execute(
        sa.text(
            """
            SELECT DISTINCT u.id
            FROM users AS u
            JOIN user_roles AS ur ON ur.user_id = u.id
            JOIN roles AS r ON r.id = ur.role_id
            WHERE lower(u.email) = lower(:source_email)
              AND r.code = :platform_owner_role
            """
        ),
        {"source_email": source_email, "platform_owner_role": PLATFORM_OWNER_ROLE},
    ).scalar_one_or_none()
    if source_owner_id is None:
        return

    target_user_id = bind.execute(
        sa.text("SELECT id FROM users WHERE lower(email) = lower(:target_email)"),
        {"target_email": target_email},
    ).scalar_one_or_none()
    if target_user_id is not None and target_user_id != source_owner_id:
        raise RuntimeError(
            f"Cannot rename Platform Owner to {target_email}: that email already belongs to another user."
        )

    bind.execute(
        sa.text("UPDATE users SET email = :target_email WHERE id = :user_id"),
        {"target_email": target_email, "user_id": source_owner_id},
    )


def upgrade() -> None:
    _rename_platform_owner_email(LEGACY_PLATFORM_OWNER_EMAIL, PLATFORM_OWNER_EMAIL)


def downgrade() -> None:
    _rename_platform_owner_email(PLATFORM_OWNER_EMAIL, LEGACY_PLATFORM_OWNER_EMAIL)