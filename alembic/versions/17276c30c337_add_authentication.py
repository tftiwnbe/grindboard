"""add authentication

Revision ID: 17276c30c337
Revises: c3c891c1a904
Create Date: 2025-09-05 04:49:26.221193

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17276c30c337'
down_revision: str | Sequence[str] |  None = 'c3c891c1a904'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('username', sa.String(length=150), nullable=False),
    sa.Column('password_hash', sa.String(length=256), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('auth_token',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('token', sa.String(length=255), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    with op.batch_alter_table('task', recreate='always') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_task_user_id_user', 'user', ['user_id'], ['id'], ondelete='CASCADE'
        )
        batch_op.create_index(op.f('ix_task_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('task', recreate='always') as batch_op:
        batch_op.drop_index(op.f('ix_task_user_id'))
        batch_op.drop_constraint('fk_task_user_id_user', type_='foreignkey')
        batch_op.drop_column('user_id')
    op.drop_table('auth_token')
    op.drop_table('user')
