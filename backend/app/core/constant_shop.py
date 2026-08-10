HEAL_COST = 20
HEAL_PERCENT = 0.5

# Проценты/множители расходников и постоянных предметов см.
# artifacts/shop-design.md — числа выведены из симуляции (8000 боёв на
# сетку профилей), не подбирались на глаз.

# ── Специализации: постоянные бонусы к боевым рычагам ──
SPEC_STRENGTH_ATTACK_MULTIPLIER = 1.05
SPEC_FOCUS_ACCURACY_MULTIPLIER = 1.10
SPEC_AGILITY_EVASION_MULTIPLIER = 1.15
SPEC_INTELLECT_CRIT_BONUS = 0.03       # п.п., до клампа CRIT_CHANCE_MAX
SPEC_HEALTH_REGEN_BONUS = 0.05         # п.п. к дневному % регена HP
EYE_FOCUS_CRIT_MULTIPLIER = 2.0        # вместо CRIT_MULTIPLIER=1.5

# ── Расходники: применяются на старте боя, не при покупке ──
RAGE_POTION_DILIGENCE_MULTIPLIER = 0.5   # attack *= 1 + это * diligence
GUARD_POTION_DAMAGE_REDUCTION = 0.15     # boss_attack *= 1 - это
SECOND_CHANCE_REVIVE_HP_PERCENT = 0.25   # доля max_hp при воскрешении
PATIENCE_EXTRA_ROUNDS = 2                # + к лимиту раундов на этот бой

# key -> категория для правила "сумки" (второй расходник — из другой
# категории). Только у расходников (permanent=False).
CONSUMABLE_CATEGORY_OFFENSIVE = "offensive"
CONSUMABLE_CATEGORY_DEFENSIVE = "defensive"
CONSUMABLE_CATEGORY_OUTCOME = "outcome"

SHOP_ITEMS = {
    "heal_100": {
        "name": "Зелье исцеления",
        "description": "Восстанавливает 100% HP",
        "cost": 45,
        "unlock_level": 5,
        "repeatable": True,
        "permanent": False,
        "category": None,
    },
    "extra_boss_fight": {
        "name": "Знак дополнительного боя",
        "description": "Позволяет сразиться с боссом ещё раз сегодня, в обход дневного лимита",
        "cost": 40,
        "unlock_level": 10,
        "repeatable": True,
        "permanent": False,
        "category": None,
    },

    # ── Расходники: заряд выдаётся при покупке, эффект — при выборе на старте боя ──
    "potion_rage": {
        "name": "Зелье ярости",
        "description": "+5% к урону за каждый закрытый сегодня квест, максимум +50%",
        "cost": 60,
        "unlock_level": 0,
        "repeatable": True,
        "permanent": False,
        "category": CONSUMABLE_CATEGORY_OFFENSIVE,
    },
    "potion_guard": {
        "name": "Оберег защиты",
        "description": "-15% урона босса на этот бой",
        "cost": 60,
        "unlock_level": 0,
        "repeatable": True,
        "permanent": False,
        "category": CONSUMABLE_CATEGORY_DEFENSIVE,
    },
    "charm_mercy": {
        "name": "Оберег пощады",
        "description": "После поражения босс не получает уровень",
        "cost": 120,
        "unlock_level": 0,
        "repeatable": True,
        "permanent": False,
        "category": CONSUMABLE_CATEGORY_OUTCOME,
    },
    "token_second_chance": {
        "name": "Знак шанса",
        "description": "После смерти — воскрешение на 25% максимума HP, один раз за бой",
        "cost": 180,
        "unlock_level": 0,
        "repeatable": True,
        "permanent": False,
        "category": CONSUMABLE_CATEGORY_DEFENSIVE,
    },
    "token_patience": {
        "name": "Знак терпения",
        "description": "+2 раунда к продолжительности боя",
        "cost": 120,
        "unlock_level": 0,
        "repeatable": True,
        "permanent": False,
        "category": CONSUMABLE_CATEGORY_OUTCOME,
    },

    # ── Постоянные: покупаются один раз, действуют всегда, заряд не расходуется ──
    "eye_focus": {
        "name": "Глаз-фокус",
        "description": "Множитель критического урона 1.5× → 2×",
        "cost": 500,
        "unlock_level": 0,
        "repeatable": False,
        "permanent": True,
        "category": None,
    },
    "bag": {
        "name": "Сумка",
        "description": "Позволяет взять в бой второй расходник — из другой категории",
        "cost": 500,
        "unlock_level": 0,
        "repeatable": False,
        "permanent": True,
        "category": None,
    },
    "spec_strength": {
        "name": "Специализация силы",
        "description": "+5% к урону атаки",
        "cost": 250,
        "unlock_level": 0,
        "repeatable": False,
        "permanent": True,
        "category": None,
    },
    "spec_focus": {
        "name": "Специализация фокуса",
        "description": "+10% к точности",
        "cost": 250,
        "unlock_level": 0,
        "repeatable": False,
        "permanent": True,
        "category": None,
    },
    "spec_agility": {
        "name": "Специализация ловкости",
        "description": "+15% к уклонению",
        "cost": 250,
        "unlock_level": 0,
        "repeatable": False,
        "permanent": True,
        "category": None,
    },
    "spec_intellect": {
        "name": "Специализация интеллекта",
        "description": "+3 п.п. к шансу крита",
        "cost": 250,
        "unlock_level": 0,
        "repeatable": False,
        "permanent": True,
        "category": None,
    },
    "spec_health": {
        "name": "Специализация здоровья",
        "description": "+5 п.п. к дневному регену HP",
        "cost": 250,
        "unlock_level": 0,
        "repeatable": False,
        "permanent": True,
        "category": None,
    },
}

# Ключи расходников, которые можно выбрать при старте боя (SHOP_ITEMS без
# heal_100/extra_boss_fight — те применяются/списываются вне боя).
FIGHT_CONSUMABLE_KEYS = frozenset({
    "potion_rage", "potion_guard", "charm_mercy",
    "token_second_chance", "token_patience",
})

PERMANENT_ITEM_KEYS = frozenset(
    key for key, item in SHOP_ITEMS.items() if item["permanent"]
)
