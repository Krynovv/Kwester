from pydantic import BaseModel, ConfigDict

from ..models.boss_fight import FightStatus, FightActor, PlayerActionType
from ..service.combat import PlayerAction


class BossStatus(BaseModel):
    boss_name: str
    boss_level: int
    boss_hp: int
    pending_failures: int
    current_hp: int
    max_hp: int
    already_fought_today: bool
    fight_window_open: bool
    projected_damage: int
    is_ready: bool


class TurnRequest(BaseModel):
    action: PlayerAction


class FightStartRequest(BaseModel):
    # Ключи SHOP_ITEMS расходников (permanent=False), выбранные на этот бой.
    # Без "сумки" — не больше одного; с ней — до двух из разных категорий.
    consumables: list[str] = []


class RoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_no: int
    actor: FightActor
    action: PlayerActionType | None
    hit: bool
    crit: bool
    damage: int
    target_hp_after: int


class FightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: FightStatus
    current_round: int
    boss_level_at_time: int
    boss_hp: int
    boss_max_hp: int
    player_hp: int
    player_max_hp: int
    damage_dealt: int
    currency_awarded: int
    xp_awarded: int
    active_consumables: list[str]
    rounds: list[RoundRead]
