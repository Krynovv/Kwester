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



def get_boss_name(level: int) -> str:
    name = BOSS_TIERS[0][1]
    for threshold, tier_name in BOSS_TIERS:
        if level >= threshold:
            name = tier_name
    return name

# ----- Структура раунда ----- #
COUNT_ROUND = 7        # лимит раундов
FIGHT_TTL_MINUTES = 30 # брошенный бой

# Порог сознательно выше дневного регена (HP_REGEN_PERCENT). Если бы они
# совпадали, после KO игрок восстанавливался бы ровно до порога и его снова
# пускали бы в бой на грани смерти — спираль поражений без выхода.
MIN_FIGHT_HP_PERCENT = 0.5 # ниже порога в бой не пускается

# Порог XP для след. уровня стата = BASE + (level - 1) * INCREMENT.
# Линейный, не экспоненциальный рост: держит прокачку в районе +2 квеста
# ("once", 15 XP) на каждый следующий уровень, начиная с 5 квестов на 1-й.
# BASE должен совпадать с Stat.xp_to_next_level.default.
STAT_LEVEL_XP_BASE = 75
STAT_LEVEL_XP_INCREMENT = 30

# ----- Игрок ----- #
BASE_MAX_HP = 100
HP_PER_HEALTH_LEVEL = 10
HP_REGEN_PERCENT = 0.2              # 20% реген

# ----- Вклад квестов ----- #
QUEST_EFFORT_CAP = 2        # не больше 2 квестов на стат.
                            # Шкала: 2 × 5 статов = 10 квестов/день это ПОТОЛОК,
                            # дальше усилия не считаются. Было 3 (=15/день) —
                            # столько никто стабильно не закрывает
EFFORT_POWER_BONUS = 0.5    # квесты дают x1.5
QUEST_COVERAGE_TARGET = 2   # норма квестов

# ----- BOSS ----- #
BOSS_TARGET_KILL_ROUNDS = 6.0  # за сколько игрок должен убивать босса
BOSS_HP_LEVEL_SCALING = 0.08   # + 8% HP за каждый уровень разрыва с игроком
BOSS_HP_SCALING_CLAMP = (0.6, 2.0)

# Урон босса задаётся так же — через "за сколько раундов он тебя убьёт".
BOSS_KILL_ROUNDS_SLACKER = 5.0    # ничего не сделал за день → смерть на 5-м
BOSS_KILL_ROUNDS_DILIGENT = 9.0   # всё сделал → босс не успевает за 7 раундов

# Эталонный игрок, от которого считаются HP и урон босса.
# ВАЖНО: это фиксированные числа, а НЕ фактические точность/крит игрока.
# Если подставить сюда реальные значения, прокачка Фокуса и Интеллекта
# начнёт ровно настолько же поднимать HP босса и обнулит сама себя.
BOSS_HP_REFERENCE_HIT = 0.75
BOSS_HP_REFERENCE_CRIT = 0.15
BOSS_HP_REFERENCE_EFFORT = 0.5    # эталон — ТИПИЧНЫЙ день (1 квест на стат,
                                  # 5 квестов), а не прогул и не потолок.
                                  # Если считать эталоном прогульщика, обычный
                                  # игрок сносит босса за 4 раунда из 7
BOSS_DAMAGE_REFERENCE_HIT = 0.70

# Рейтинги босса: идут в знаменатель ACC/(ACC+dodge), а не вычитаются из шанса.
BOSS_DODGE_RATING_PER_LEVEL = 0.6
BOSS_ACCURACY_RATING_PER_LEVEL = 2.5

BOSS_TIERS = [
    (1, "Гоблин"),
    (5, "Огр"),
    (15, "Голем"),
    (25, "Темный колдун"),
    (50, "Дракон"),
]

# ────────────────────────── Попадания и криты (новое) ─────────────────────
# Нижний порог высокий намеренно: при 7 раундах один промах = 14% боя,
HIT_CHANCE_MIN = 0.55
HIT_CHANCE_MAX = 0.95
BOSS_HIT_CHANCE_MIN = 0.45
BOSS_HIT_CHANCE_MAX = 0.85

CRIT_CHANCE_BASE = 0.05
CRIT_CHANCE_PER_INTELLECT_LEVEL = 0.02
CRIT_CHANCE_MAX = 0.40
CRIT_MULTIPLIER = 1.5         # крит ЗАМЕНЯЕТ обычный урон, а не прибавляется

ACTION_JOKE_DAMAGE_MULTIPLIER = 0.6
ACTION_JOKE_CRIT_MULTIPLIER = 2.0
ACTION_EXCUSE_EVASION_MULTIPLIER = 2.0

# ----- Исходы боя и смерть (новое) ------
DEATH_BOSS_LEVEL_GAIN = 1         # KO → босс подрастёт к следующему бою
# Потолок разрыва между уровнем босса и средним уровнем боевых статов игрока.
# Без него отстающий игрок никогда не догоняет: разрыв растёт на +1 за
# каждое KO, а сам игрок прокачивается кратно медленнее (xp_to_next_level
# растёт экспоненциально). +4 уровня разрыва уже требуют 7.7 раунда на
# убийство при лимите COUNT_ROUND=7 — чистая победа становится недостижима.
BOSS_LEVEL_GAP_CAP = 3
TIMEOUT_POINTS_WIN_REWARD = 0.5   # победа по очкам на таймауте → половина награды
EXHAUSTED_REWARD_MULTIPLIER = 0.5 # ⚠️ при hp==0 режет награды за КВЕСТЫ вдвое.

OFF_SCHEDULE_HP_PENALTY = 5         # HP за выполнение привычки вне её расписания
STREAK_LOOKBACK_DAYS = 30           # вглубь скольких дней ищем пропуски расписания
SECONDARY_STAT_XP_SHARE = 0.5       # доля XP для второго стата квеста

# ----- Награда ----- #
WIN_BASE_CURRENCY = 20
WIN_CURRENCY_PER_BOSS_LEVEL = 5
WIN_CURRENCY_PER_INTELLECT = 2 
WIN_BASE_XP = 50

BOSS_STATUS_CACHE_TTL = 30 # Время актуальности статуса для Redis
FIGHT_WINDOW_START_HOUR = 17

ALLOWED_AVATAR_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024
# Потолок на тело любого запроса. Аватар — самая тяжёлая загрузка в API,
# плюс запас на multipart-обвязку. Проверяется до разбора тела, иначе
# Starlette успевает слить гигабайты во временный файл на диске.
MAX_REQUEST_BODY_SIZE = MAX_AVATAR_SIZE + 1024 * 1024

# SHOP_ITEMS переехал в constant_shop.py вместе с редизайном магазина —
# permanent/category полей тут не было, а новые предметы (расходники,
# специализации) без них не работают.
