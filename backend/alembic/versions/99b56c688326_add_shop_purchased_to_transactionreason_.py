"""add shop_purchased to transactionreason enum

Revision ID: 99b56c688326
Revises: 604edba05030
Create Date: 2026-07-12 14:51:21.008637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99b56c688326'
down_revision: Union[str, Sequence[str], None] = '604edba05030'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE transactionreason ADD VALUE 'shop_purchased'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
