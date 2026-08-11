"""merge shop-redesign and main heads

Revision ID: 462cefb6a222
Revises: a3f1c72d5b48, dc215cac2917
Create Date: 2026-08-11 11:02:44.467387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '462cefb6a222'
down_revision: Union[str, Sequence[str], None] = ('a3f1c72d5b48', 'dc215cac2917')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
