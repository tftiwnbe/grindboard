"""add tag unique constraint and cascade delete

Revision ID: 3a9f1b2c4d5e
Revises: cf308266d562
Create Date: 2026-04-22 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlmodel.sql import sqltypes


revision: str = "3a9f1b2c4d5e"
down_revision: str | Sequence[str] | None = "cf308266d562"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Recreate tags table with CASCADE delete and unique(user_id, name)."""
    with op.batch_alter_table("tags", recreate="always") as batch_op:
        batch_op.create_foreign_key(
            "fk_tags_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint("uq_tags_user_name", ["user_id", "name"])


def downgrade() -> None:
    """Revert to tags table without CASCADE or unique constraint."""
    with op.batch_alter_table("tags", recreate="always") as batch_op:
        batch_op.drop_constraint("uq_tags_user_name", type_="unique")
        batch_op.drop_constraint("fk_tags_user_id", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_tags_user_id_plain",
            "users",
            ["user_id"],
            ["id"],
        )
