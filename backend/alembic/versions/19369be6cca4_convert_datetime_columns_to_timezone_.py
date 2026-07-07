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
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE quests ALTER COLUMN date_start TYPE TIMESTAMPTZ USING date_start AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE quests ALTER COLUMN date_end TYPE TIMESTAMPTZ USING date_end AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE quests ALTER COLUMN last_completed_at TYPE TIMESTAMPTZ USING last_completed_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE transaction_logs ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE quests ALTER COLUMN date_start TYPE TIMESTAMP USING date_start AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE quests ALTER COLUMN date_end TYPE TIMESTAMP USING date_end AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE quests ALTER COLUMN last_completed_at TYPE TIMESTAMP USING last_completed_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE transaction_logs ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'")
