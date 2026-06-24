"""add tasks user position index

Revision ID: 7f6b5d4c3a21
Revises: d1e2f3a4b5c6
Create Date: 2026-06-24 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op


revision: str = "7f6b5d4c3a21"
down_revision: str | Sequence[str] | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_tasks_user_id_position",
        "tasks",
        ["user_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_tasks_user_id_position", table_name="tasks")
