"""add position column to tasks

Revision ID: c6387905b36d
Revises: a27e17b3719f
Create Date: 2026-01-12 22:35:29.571081

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c6387905b36d"
down_revision: str | Sequence[str] | None = "a27e17b3719f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(
            sa.Column("position", sa.Float(), nullable=True, index=True)
        )

    # Backfill existing tasks per user
    # order by user_id, then task id
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id, user_id FROM tasks ORDER BY user_id, id"))

    last_positions: dict[int, float] = {}
    for row in result:
        user_id = row.user_id
        pos = last_positions.get(user_id, 0.0)
        conn.execute(
            sa.text("UPDATE tasks SET position = :pos WHERE id = :id"),
            {"pos": pos, "id": row.id},
        )
        last_positions[user_id] = pos + 1.0  # increment for next task of same user

    # Make column NOT NULL
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column("position", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("position")
