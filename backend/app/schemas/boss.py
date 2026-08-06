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
    rounds: list[RoundRead]
