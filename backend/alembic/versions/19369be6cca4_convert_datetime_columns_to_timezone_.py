"""convert datetime columns to timezone-aware

Revision ID: 19369be6cca4
Revises: bf61db68332e
Create Date: 2026-07-07 11:17:23.364361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19369be6cca4'
down_revision: Union[str, Sequence[str], None] = 'bf61db68332e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
