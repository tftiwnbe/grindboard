"""add completed_at and deadline to tasks

Revision ID: d1e2f3a4b5c6
Revises: 3a9f1b2c4d5e
Create Date: 2026-04-23 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: str | Sequence[str] | None = "3a9f1b2c4d5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("deadline", sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("deadline")
        batch_op.drop_column("completed_at")
