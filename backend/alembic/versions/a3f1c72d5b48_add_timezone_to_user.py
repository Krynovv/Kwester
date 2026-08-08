"""add timezone to user

Revision ID: a3f1c72d5b48
Revises: 225ca2596e23
Create Date: 2026-08-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f1c72d5b48'
down_revision: Union[str, Sequence[str], None] = '225ca2596e23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default='UTC' сохраняет прежнее поведение для всех, кто
    # зарегистрировался до появления поля.
    op.add_column(
        'users',
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='UTC'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'timezone')
