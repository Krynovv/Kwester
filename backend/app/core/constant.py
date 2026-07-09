from ..models.stat import CombatRole

DEFAULT_STATS = [
    {"name": "Сила", "combat_role": CombatRole.strength},
    {"name": "Ловкость", "combat_role": CombatRole.agility},
    {"name": "Интелект", "combat_role": CombatRole.intellect},
    {"name": "Фокус", "combat_role": CombatRole.focus},
    {"name": "Здоровье", "combat_role": CombatRole.health},
]

BOSS_TIERS = [
    (1, "Гоблин"),
    (5, "Огр"),
    (10, "Голем"),
    (20, "Темный колдун"),
    (40, "Дракон"),
]

BASE_MAX_HP = 100
HP_PER_HEALTH_LEVEL = 10
HP_REGEN_PERCENT = 0.2              # 20% реген


BOSS_BASE_HP = 100
BOSS_HP_PER_LEVEL = 20            
EXHAUSTED_REWARD_MULTIPLIER = 0.5   # штраф наград

WIN_BASE_CURRENCY = 20
WIN_CURRENCY_PER_BOSS_LEVEL = 5 
WIN_BASE_XP = 50

HEAL_COST = 20
HEAL_PERCENT = 0.5

FIGHT_WINDOW_START_HOUR = 17

