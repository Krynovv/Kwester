"""Боевая математика: чистые функции, без БД и побочных эффектов.

Главный принцип: HP и урон босса не задаются напрямую, а ВЫВОДЯТСЯ из
целевой длины боя (BOSS_TARGET_KILL_ROUNDS, BOSS_KILL_ROUNDS_*). Константы
описывают ощущение боя — "босс умирает за 6 раундов", "прогульщик умирает
на 4-м" — а конкретные числа считаются отсюда.

Роли статов:
    Сила      → урон атаки
    Фокус     → точность
    Ловкость  → уклонение
    Интеллект → крит (и валюта за победу)
    Здоровье  → пул HP
"""

import enum
import math
import random
from dataclasses import dataclass

from ..core.constant import (
    ACTION_JOKE_DAMAGE_MULTIPLIER, ACTION_JOKE_CRIT_MULTIPLIER,
    ACTION_EXCUSE_EVASION_MULTIPLIER,
    BASE_MAX_HP, HP_PER_HEALTH_LEVEL,
    QUEST_EFFORT_CAP, EFFORT_POWER_BONUS,
    HIT_CHANCE_MIN, HIT_CHANCE_MAX,
    BOSS_HIT_CHANCE_MIN, BOSS_HIT_CHANCE_MAX,
    CRIT_CHANCE_BASE, CRIT_CHANCE_PER_INTELLECT_LEVEL, CRIT_CHANCE_MAX,
    CRIT_MULTIPLIER,
    BOSS_TARGET_KILL_ROUNDS, BOSS_HP_LEVEL_SCALING, BOSS_HP_SCALING_CLAMP,
    BOSS_KILL_ROUNDS_SLACKER, BOSS_KILL_ROUNDS_DILIGENT,
    BOSS_HP_REFERENCE_HIT, BOSS_HP_REFERENCE_CRIT, BOSS_HP_REFERENCE_EFFORT,
    BOSS_DAMAGE_REFERENCE_HIT,
    BOSS_DODGE_RATING_PER_LEVEL, BOSS_ACCURACY_RATING_PER_LEVEL,
)
from ..core.constant_shop import (
    SPEC_STRENGTH_ATTACK_MULTIPLIER, SPEC_FOCUS_ACCURACY_MULTIPLIER,
    SPEC_AGILITY_EVASION_MULTIPLIER, SPEC_INTELLECT_CRIT_BONUS,
    EYE_FOCUS_CRIT_MULTIPLIER,
)
from ..models.stat import CombatRole


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def quest_effort(completed: int) -> float:
    """Вклад дневных квестов по стату, 0..1. Сверх QUEST_EFFORT_CAP не считаем —
    иначе двадцать квестов "попил воды" превращаются в ваншот босса."""
    return min(completed, QUEST_EFFORT_CAP) / QUEST_EFFORT_CAP


def stat_power(level: int, effort: float) -> float:
    """Уровень стата, усиленный дневными квестами: ×1.0 .. ×1.5."""
    return level * (1 + EFFORT_POWER_BONUS * effort)


@dataclass(frozen=True)
class PlayerCombat:
    attack: float           # Сила
    accuracy: float         # Фокус
    evasion: float          # Ловкость
    crit_chance: float      # Интеллект
    max_hp: int             # Здоровье
    avg_level: float        # средний уровень боевых статов — масштаб босса
    diligence: float        # 0..1, средний effort по всем статам за день
    # eye_focus меняет фактический крит игрока, не эталон урона босса
    # (calculate_boss_hp продолжает использовать глобальный CRIT_MULTIPLIER) —
    # иначе прокачка крита задним числом подняла бы HP босса и обнулила себя.
    crit_multiplier: float = CRIT_MULTIPLIER


def build_player_combat(
    levels: dict[CombatRole, int],
    quests_completed: dict[CombatRole, int],
    owned_permanent: frozenset[str] = frozenset(),
) -> PlayerCombat:
    efforts = {role: quest_effort(quests_completed.get(role, 0)) for role in CombatRole}
    power = {role: stat_power(levels.get(role, 0), efforts[role]) for role in CombatRole}

    attack = power[CombatRole.strength]
    accuracy = power[CombatRole.focus]
    evasion = power[CombatRole.agility]
    crit = CRIT_CHANCE_BASE + CRIT_CHANCE_PER_INTELLECT_LEVEL * power[CombatRole.intellect]

    if "spec_strength" in owned_permanent:
        attack *= SPEC_STRENGTH_ATTACK_MULTIPLIER
    if "spec_focus" in owned_permanent:
        accuracy *= SPEC_FOCUS_ACCURACY_MULTIPLIER
    if "spec_agility" in owned_permanent:
        evasion *= SPEC_AGILITY_EVASION_MULTIPLIER
    if "spec_intellect" in owned_permanent:
        crit += SPEC_INTELLECT_CRIT_BONUS

    return PlayerCombat(
        attack=attack,
        accuracy=accuracy,
        evasion=evasion,
        crit_chance=_clamp(crit, CRIT_CHANCE_BASE, CRIT_CHANCE_MAX),
        crit_multiplier=EYE_FOCUS_CRIT_MULTIPLIER if "eye_focus" in owned_permanent else CRIT_MULTIPLIER,
        max_hp=calculate_max_hp(levels.get(CombatRole.health, 0)),
        avg_level=sum(levels.get(role, 0) for role in CombatRole) / len(CombatRole),
        diligence=sum(efforts.values()) / len(efforts),
    )


def calculate_max_hp(health_level: int) -> int:
    return BASE_MAX_HP + health_level * HP_PER_HEALTH_LEVEL


def hit_chance_on_boss(accuracy: float, boss_level: int) -> float:
    """Соотношение, а не разность: шанс никогда не схлопывается в 0 или 1."""
    dodge = boss_level * BOSS_DODGE_RATING_PER_LEVEL
    if accuracy + dodge <= 0:
        return HIT_CHANCE_MIN
    return _clamp(accuracy / (accuracy + dodge), HIT_CHANCE_MIN, HIT_CHANCE_MAX)


def hit_chance_on_player(evasion: float, boss_level: int) -> float:
    boss_accuracy = boss_level * BOSS_ACCURACY_RATING_PER_LEVEL
    if boss_accuracy + evasion <= 0:
        return BOSS_HIT_CHANCE_MIN
    return _clamp(
        boss_accuracy / (boss_accuracy + evasion),
        BOSS_HIT_CHANCE_MIN,
        BOSS_HIT_CHANCE_MAX,
    )


def expected_damage_per_round(player: PlayerCombat, boss_level: int) -> float:
    """Средний урон игрока за раунд с учётом промахов и критов."""
    hit = hit_chance_on_boss(player.accuracy, boss_level)
    crit_bonus = 1 + player.crit_chance * (CRIT_MULTIPLIER - 1)
    return hit * player.attack * crit_bonus


def calculate_boss_hp(player_avg_level: float, boss_level: int) -> int:
    """HP босса = столько, чтобы эталонный игрок такого уровня убивал его
    за BOSS_TARGET_KILL_ROUNDS раундов, с поправкой на разрыв в уровнях."""
    reference_dps = (
        stat_power(player_avg_level, BOSS_HP_REFERENCE_EFFORT)
        * BOSS_HP_REFERENCE_HIT
        * (1 + BOSS_HP_REFERENCE_CRIT * (CRIT_MULTIPLIER - 1))
    )
    scaling = _clamp(
        1 + BOSS_HP_LEVEL_SCALING * (boss_level - player_avg_level),
        *BOSS_HP_SCALING_CLAMP,
    )
    return max(1, round(BOSS_TARGET_KILL_ROUNDS * reference_dps * scaling))


def calculate_boss_attack(player_max_hp: int, diligence: float) -> int:
    """Урон босса за попадание. Задан через "за сколько раундов он тебя убьёт":
    прогульщик умирает на 4-м, прилежный не умирает за 7 вовсе.

    Делим на эталонный шанс попадания, а не на фактический. Иначе прокачка
    Ловкости снижала бы шанс и ровно настолько же поднимала урон за удар.
    """
    kill_rounds = BOSS_KILL_ROUNDS_SLACKER + (
        BOSS_KILL_ROUNDS_DILIGENT - BOSS_KILL_ROUNDS_SLACKER
    ) * _clamp(diligence, 0.0, 1.0)
    return max(1, round(player_max_hp / (kill_rounds * BOSS_DAMAGE_REFERENCE_HIT)))


# ─────────────────────────── Разрешение раунда ────────────────────────────
# Раунд = фаза игрока, затем фаза босса. Игрок всегда ходит первым; если он
# добивает босса в свою фазу, босс не отвечает.

class PlayerAction(str, enum.Enum):
    attack = "attack"   # Сила: полный урон
    joke = "joke"       # Интеллект: меньше урона, вдвое выше крит, крит затыкает босса
    excuse = "excuse"   # Ловкость: урона нет, удваивает уклонение на ответ босса


@dataclass(frozen=True)
class TurnOutcome:
    hit: bool
    crit: bool
    damage: int
    roll: float
    stuns_boss: bool = False      # босс пропускает свою фазу
    evasion_bonus: bool = False   # уклонение удваивается на ближайшую атаку босса


def round_rng(seed: str, round_no: int, actor: str) -> random.Random:
    """Броски детерминированы от (seed, номер раунда, кто ходит).

    Так бой воспроизводится для показа переписки заново, и игрок не может
    переспросить ход, чтобы перекатить крит: результат уже предопределён.
    """
    return random.Random(f"{seed}:{round_no}:{actor}")


def resolve_player_turn(
    player: PlayerCombat,
    boss_level: int,
    action: PlayerAction,
    rng: random.Random,
) -> TurnOutcome:
    if action is PlayerAction.excuse:
        return TurnOutcome(hit=False, crit=False, damage=0, roll=0.0, evasion_bonus=True)

    roll = rng.random()
    if roll >= hit_chance_on_boss(player.accuracy, boss_level):
        return TurnOutcome(hit=False, crit=False, damage=0, roll=roll)

    crit_chance = player.crit_chance
    attack = player.attack
    if action is PlayerAction.joke:
        crit_chance = min(crit_chance * ACTION_JOKE_CRIT_MULTIPLIER, CRIT_CHANCE_MAX)
        attack *= ACTION_JOKE_DAMAGE_MULTIPLIER

    crit = rng.random() < crit_chance
    # Округляем один раз в самом конце, floor: иначе дроби текут через все шаги.
    damage = max(1, math.floor(attack * (player.crit_multiplier if crit else 1.0)))

    return TurnOutcome(
        hit=True,
        crit=crit,
        damage=damage,
        roll=roll,
        stuns_boss=crit and action is PlayerAction.joke,
    )


def resolve_boss_turn(
    player: PlayerCombat,
    boss_level: int,
    boss_attack: int,
    rng: random.Random,
    evasion_bonus: bool = False,
) -> TurnOutcome:
    evasion = player.evasion * (ACTION_EXCUSE_EVASION_MULTIPLIER if evasion_bonus else 1.0)
    roll = rng.random()
    if roll >= hit_chance_on_player(evasion, boss_level):
        return TurnOutcome(hit=False, crit=False, damage=0, roll=roll)
    return TurnOutcome(hit=True, crit=False, damage=boss_attack, roll=roll)
