"""fix quest_completed enum typo

Revision ID: 28f0cf6fe5ff
Revises: 1e5ac0aa7e31
Create Date: 2026-07-05 12:58:23.562607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28f0cf6fe5ff'
down_revision: Union[str, Sequence[str], None] = '1e5ac0aa7e31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE transactionreason RENAME VALUE 'quest_comleted' TO 'quest_completed'")


def downgrade() -> None:
    op.execute("ALTER TYPE transactionreason RENAME VALUE 'quest_completed' TO 'quest_comleted'")
