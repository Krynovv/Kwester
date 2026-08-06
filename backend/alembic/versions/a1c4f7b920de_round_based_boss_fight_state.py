"""round based boss fight state

Превращает boss_fights из записи результата в состояние боя и добавляет
пораундовый лог boss_fight_rounds.

Миграция аддитивная: старые бои сохраняются. Полей пошагового боя у них
физически неоткуда взять, поэтому заполняются заглушками (rng_seed пустой,
snapshot пустой, HP игрока 0) — воспроизвести такой бой нельзя, но история
остаётся видимой.

Revision ID: a1c4f7b920de
Revises: b31ee37e62dc
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1c4f7b920de'
down_revision: Union[str, Sequence[str], None] = 'b31ee37e62dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


fight_status = postgresql.ENUM(
    'active', 'won', 'lost', 'timeout', name='fightstatus', create_type=False
)
fight_actor = postgresql.ENUM('player', 'boss', name='fightactor', create_type=False)
player_action = postgresql.ENUM(
    'attack', 'joke', 'excuse', name='playeractiontype', create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    fight_status.create(bind, checkfirst=True)
    fight_actor.create(bind, checkfirst=True)
    player_action.create(bind, checkfirst=True)

    # 1. Новые колонки — сначала nullable, чтобы existing rows не падали.
    op.add_column('boss_fights', sa.Column('boss_max_hp', sa.Integer(), nullable=True))
    op.add_column('boss_fights', sa.Column('boss_attack', sa.Integer(), nullable=True))
    op.add_column('boss_fights', sa.Column('player_hp_start', sa.Integer(), nullable=True))
    op.add_column('boss_fights', sa.Column('player_hp', sa.Integer(), nullable=True))
    op.add_column('boss_fights', sa.Column('player_max_hp', sa.Integer(), nullable=True))
    op.add_column('boss_fights', sa.Column('stats_snapshot', sa.JSON(), nullable=True))
    op.add_column('boss_fights', sa.Column('rng_seed', sa.String(length=64), nullable=True))
    op.add_column('boss_fights', sa.Column('status', fight_status, nullable=True))
    op.add_column('boss_fights', sa.Column('current_round', sa.Integer(), nullable=True))
    op.add_column('boss_fights', sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('boss_fights', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('boss_fights', sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True))

    # 2. Бэкфилл старых записей.
    op.execute("""
        UPDATE boss_fights SET
            boss_max_hp     = boss_hp,
            boss_attack     = 0,
            player_hp_start = 0,
            player_hp       = 0,
            player_max_hp   = 0,
            stats_snapshot  = '{}'::json,
            rng_seed        = '',
            status          = CASE result
                                  WHEN 'won'  THEN 'won'::fightstatus
                                  WHEN 'lost' THEN 'lost'::fightstatus
                                  ELSE 'timeout'::fightstatus
                              END,
            current_round   = 0,
            started_at      = fight_date::timestamptz,
            expires_at      = fight_date::timestamptz,
            finished_at     = fight_date::timestamptz
    """)

    # 3. Теперь можно требовать NOT NULL.
    for column in (
        'boss_max_hp', 'boss_attack', 'player_hp_start', 'player_hp',
        'player_max_hp', 'stats_snapshot', 'rng_seed', 'status',
        'current_round', 'started_at', 'expires_at',
    ):
        op.alter_column('boss_fights', column, nullable=False)

    op.drop_column('boss_fights', 'result')
    op.create_index(op.f('ix_boss_fights_user_id'), 'boss_fights', ['user_id'])

    # 4. Пораундовый лог.
    op.create_table(
        'boss_fight_rounds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fight_id', sa.Integer(), nullable=False),
        sa.Column('round_no', sa.Integer(), nullable=False),
        sa.Column('actor', fight_actor, nullable=False),
        sa.Column('action', player_action, nullable=True),
        sa.Column('roll', sa.Float(), nullable=False),
        sa.Column('hit', sa.Boolean(), nullable=False),
        sa.Column('crit', sa.Boolean(), nullable=False),
        sa.Column('damage', sa.Integer(), nullable=False),
        sa.Column('target_hp_after', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['fight_id'], ['boss_fights.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_boss_fight_rounds_fight_id'), 'boss_fight_rounds', ['fight_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_boss_fight_rounds_fight_id'), table_name='boss_fight_rounds')
    op.drop_table('boss_fight_rounds')

    op.add_column('boss_fights', sa.Column('result', sa.String(length=20), nullable=True))
    op.execute("UPDATE boss_fights SET result = status::text")

    op.drop_index(op.f('ix_boss_fights_user_id'), table_name='boss_fights')
    for column in (
        'finished_at', 'expires_at', 'started_at', 'current_round', 'status',
        'rng_seed', 'stats_snapshot', 'player_max_hp', 'player_hp',
        'player_hp_start', 'boss_attack', 'boss_max_hp',
    ):
        op.drop_column('boss_fights', column)

    bind = op.get_bind()
    player_action.drop(bind, checkfirst=True)
    fight_actor.drop(bind, checkfirst=True)
    fight_status.drop(bind, checkfirst=True)
