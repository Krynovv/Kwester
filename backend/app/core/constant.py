from ..models.stat import CombatRole

DEFAULT_STATS = [
    {"name": "Сила", "combat_role": CombatRole.strength},
    {"name": "Ловкость", "combat_role": CombatRole.agility},
    {"name": "Интелект", "combat_role": CombatRole.intellect},
    {"name": "Фокус", "combat_role": CombatRole.focus},
    {"name": "Здоровье", "combat_role": CombatRole.health},
]
