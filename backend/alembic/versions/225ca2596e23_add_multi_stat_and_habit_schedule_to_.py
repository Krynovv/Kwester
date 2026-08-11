"""add multi-stat and habit schedule/streak fields to quest

Revision ID: 225ca2596e23
Revises: b31ee37e62dc
Create Date: 2026-08-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '225ca2596e23'
down_revision: Union[str, Sequence[str], None] = 'b31ee37e62dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('quests', sa.Column('stat_id_2', sa.Integer(), nullable=True))
    op.add_column('quests', sa.Column('scheduled_days', postgresql.ARRAY(sa.Integer()), nullable=True))
    op.add_column('quests', sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('quests', sa.Column('best_streak', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('quests', sa.Column('streak_checked_until', sa.Date(), nullable=True))
    op.create_foreign_key(
        'quests_stat_id_2_fkey', 'quests', 'stats', ['stat_id_2'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('quests_stat_id_2_fkey', 'quests', type_='foreignkey')
    op.drop_column('quests', 'streak_checked_until')
    op.drop_column('quests', 'best_streak')
    op.drop_column('quests', 'current_streak')
    op.drop_column('quests', 'scheduled_days')
    op.drop_column('quests', 'stat_id_2')
