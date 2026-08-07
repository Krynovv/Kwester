from ..models.stat import CombatRole
from ..models.quest import QuestType

QUEST_TYPE_REWARDS = {
    QuestType.once: {"currency": 10, "xp": 15},
    QuestType.daily: {"currency": 5, "xp": 8},
    QuestType.weekly: {"currency": 20, "xp": 30},
    QuestType.habit: {"currency": 3, "xp": 5},
}

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

def get_boss_name(level: int) -> str:
    name = BOSS_TIERS[0][1]
    for threshold, tier_name in BOSS_TIERS:
        if level >= threshold:
            name = tier_name
    return name

BASE_MAX_HP = 100
HP_PER_HEALTH_LEVEL = 10
HP_REGEN_PERCENT = 0.2              # 20% реген


BOSS_BASE_HP = 100
BOSS_HP_PER_LEVEL = 20            
EXHAUSTED_REWARD_MULTIPLIER = 0.5   # штраф наград

OFF_SCHEDULE_HP_PENALTY = 5         # HP за выполнение привычки вне её расписания
STREAK_LOOKBACK_DAYS = 30           # вглубь скольких дней ищем пропуски расписания
SECONDARY_STAT_XP_SHARE = 0.5       # доля XP для второго стата квеста

WIN_BASE_CURRENCY = 20
WIN_CURRENCY_PER_BOSS_LEVEL = 5 
WIN_BASE_XP = 50

HEAL_COST = 20
HEAL_PERCENT = 0.5

FIGHT_WINDOW_START_HOUR = 17

SHOP_ITEMS = {
    "heal_100": {
        "name": "Эликсир полного исцеления",
        "description": "Восстанавливает 100% HP",
        "cost": 45,
        "unlock_level": 5,
        "repeatable": True,
    },
    "extra_boss_fight": {
        "name": "Знак дополнительного боя",
        "description": "Позволяет сразиться с боссом ещё раз сегодня, в обход дневного лимита",
        "cost": 40,
        "unlock_level": 10,
        "repeatable": True,
    },
}

