"""add telegram_chat_id to user and reminder_times/last_notified_date to quest

Revision ID: f3b8c1a29e6d
Revises: a4e1f2c9d7b3
Create Date: 2026-09-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f3b8c1a29e6d'
down_revision: Union[str, Sequence[str], None] = 'a4e1f2c9d7b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('telegram_chat_id', sa.BigInteger(), nullable=True))
    op.create_unique_constraint('users_telegram_chat_id_key', 'users', ['telegram_chat_id'])

    op.add_column('quests', sa.Column('reminder_times', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('quests', sa.Column('last_notified_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('quests', 'last_notified_date')
    op.drop_column('quests', 'reminder_times')

    op.drop_constraint('users_telegram_chat_id_key', 'users', type_='unique')
    op.drop_column('users', 'telegram_chat_id')
