from pydantic import BaseModel

class BossStatus(BaseModel):
    boss_name: str
    boss_level: int 
    boss_hp: int
    pending_failures: int
    current_hp: int
    max_hp: int
    already_fought_today: bool
    fight_window_open: bool

class BossFightResult(BaseModel):
    result: str
    damage_dealt: int
    boss_hp: int
    boss_level_at_time: int
