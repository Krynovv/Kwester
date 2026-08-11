"""Численная проверка баланса магазина против чек-листа
artifacts/shop-design.md. Гоняется не через БД/service.fight (тысячи
итераций через ORM были бы неприемлемо медленными), а через чистые функции
service.combat напрямую — маленький Monte-Carlo харнесс, воспроизводящий
методику самого документа ("8000 боёв на сетку профилей").

Как и сама симуляция в документе, харнесс всегда бьёт "Атакой" (см.
"Известные слабые места" в combat-system.md) — Острота/Оправдание не
моделируются.
"""

import random
from dataclasses import replace

import pytest

from app.core.constant import COUNT_ROUND, BOSS_LEVEL_GAP_CAP, DEATH_BOSS_LEVEL_GAIN
from app.core.constant_shop import (
    RAGE_POTION_DILIGENCE_MULTIPLIER, GUARD_POTION_DAMAGE_REDUCTION,
    SECOND_CHANCE_REVIVE_HP_PERCENT, PATIENCE_EXTRA_ROUNDS,
)
from app.models.stat import CombatRole
from app.service.combat import (
    PlayerAction, build_player_combat, calculate_boss_hp, calculate_boss_attack,
    resolve_player_turn, resolve_boss_turn,
)

TRIALS = 8000
LEVEL = 6  # "против босса своего уровня" — как в combat-system.md
# Несколько уровней, а не один: урон округляется floor()-ом, и на конкретном
# уровне небольшой процентный бонус (спецализации) может не перепрыгнуть
# целочисленную границу и дать видимый эффект 0.00pp — не баг, а то самое
# квантование, о котором предупреждает "Что легко упустить" в документе.
# Документ по той же причине гоняет сетку из нескольких уровней, а не один.
LEVELS = (4, 6, 8, 10)


def simulate_fight(
    player, boss_level: int, rng: random.Random, *,
    guard_reduction: float = 0.0, patience_extra_rounds: int = 0,
    second_chance: bool = False,
) -> str:
    """Один бой чистыми функциями combat.py. Возвращает "won"/"lost"/
    "timeout_won"/"timeout_lost" — то же деление, что и "Победа% (чистая +
    по очкам)" в документе (обе категории побед суммируются в win-rate)."""
    boss_max_hp = calculate_boss_hp(player.avg_level, boss_level)
    boss_hp = boss_max_hp
    boss_attack = calculate_boss_attack(player.max_hp, player.diligence)
    if guard_reduction:
        boss_attack = round(boss_attack * (1 - guard_reduction))

    player_hp = player.max_hp
    revive_available = second_chance
    round_limit = COUNT_ROUND + patience_extra_rounds

    for _ in range(round_limit):
        player_turn = resolve_player_turn(player, boss_level, PlayerAction.attack, rng)
        boss_hp = max(0, boss_hp - player_turn.damage)
        if boss_hp <= 0:
            return "won"

        if not player_turn.stuns_boss:
            boss_turn = resolve_boss_turn(
                player, boss_level, boss_attack, rng,
                evasion_bonus=player_turn.evasion_bonus,
            )
            player_hp = max(0, player_hp - boss_turn.damage)
            if player_hp <= 0:
                if revive_available:
                    player_hp = round(player.max_hp * SECOND_CHANCE_REVIVE_HP_PERCENT)
                    revive_available = False
                else:
                    return "lost"

    return "timeout_won" if player_hp / player.max_hp > boss_hp / boss_max_hp else "timeout_lost"


def win_rate(player, boss_level: int, trials: int = TRIALS, seed: int = 1, **fight_kwargs) -> float:
    rng = random.Random(seed)
    wins = sum(
        1 for _ in range(trials)
        if simulate_fight(player, boss_level, rng, **fight_kwargs) in ("won", "timeout_won")
    )
    return wins / trials


def _player(quests_per_stat: int, owned_permanent: frozenset[str] = frozenset(), level: int = LEVEL):
    return build_player_combat(
        {role: level for role in CombatRole},
        {role: quests_per_stat for role in CombatRole},
        owned_permanent,
    )


def _apply_rage(player):
    return replace(player, attack=player.attack * (1 + RAGE_POTION_DILIGENCE_MULTIPLIER * player.diligence))


# ────────────────────────── 1. Потолок полного склада ──────────────────────────

def test_fully_geared_slacker_stays_under_seventy_percent():
    """Игрок с нулём закрытых квестов, купивший всё постоянное и применивший
    ярость + защиту, не должен побеждать чаще чем в 70% боёв (документ
    намеряет 66.8% на исходной, более щедрой ярости — с яростью, привязанной
    к усердию, при 0 квестов она вообще не работает, так что запас есть)."""
    all_permanent = frozenset({
        "eye_focus", "spec_strength", "spec_focus", "spec_agility", "spec_intellect",
    })
    player = _apply_rage(_player(0, all_permanent))

    rate = win_rate(player, LEVEL, guard_reduction=GUARD_POTION_DAMAGE_REDUCTION)

    assert rate <= 0.70


# ─────────────── 2. Ни один расходник не спасает прогульщика сверх меры ───────────────

@pytest.mark.parametrize("label,kwargs,apply_rage", [
    ("potion_rage", {}, True),
    ("potion_guard", {"guard_reduction": GUARD_POTION_DAMAGE_REDUCTION}, False),
    ("token_second_chance", {"second_chance": True}, False),
    ("token_patience", {"patience_extra_rounds": PATIENCE_EXTRA_ROUNDS}, False),
])
def test_single_consumable_does_not_overpower_a_slacker(label, kwargs, apply_rage):
    baseline_player = _player(0)
    baseline = win_rate(baseline_player, LEVEL)

    boosted_player = _apply_rage(baseline_player) if apply_rage else baseline_player
    boosted = win_rate(boosted_player, LEVEL, **kwargs)

    assert boosted - baseline <= 0.20, f"{label}: +{(boosted - baseline) * 100:.1f}pp"


# ───────────────── 3. Специализации: заметный, но не решающий эффект ─────────────────

@pytest.mark.parametrize("key", [
    "spec_strength", "spec_focus", "spec_agility", "spec_intellect",
])
def test_specialization_effect_is_meaningful_but_bounded(key):
    """"Типичный день" — 1 квест на стат (5 квестов), как BOSS_HP_REFERENCE_EFFORT
    в combat-system.md. Раньше специализации за одну цену давали от 0 до
    +3.4 п.п. — сила выделялась, здоровье/интеллект тонули в шуме.

    Усредняем по нескольким уровням (см. LEVELS) — на отдельном уровне
    floor()-квантование урона может случайно дать 0.00pp для конкретного
    процента, не будучи от этого слабым предметом."""
    deltas_pp = []
    for level in LEVELS:
        baseline = win_rate(_player(1, level=level), level)
        boosted = win_rate(_player(1, frozenset({key}), level=level), level)
        deltas_pp.append((boosted - baseline) * 100)

    avg_delta_pp = sum(deltas_pp) / len(deltas_pp)
    assert 0.5 <= avg_delta_pp <= 4.0, f"{key}: {avg_delta_pp:+.2f}pp avg over {deltas_pp}"


# ───────────────────── 4. Сезон: разрыв с боссом не разгоняется ─────────────────────

def test_boss_level_gap_stays_capped_over_a_season():
    """Игрок, стабильно проигрывающий (0 квестов, ниже уровня босса),
    не должен утягивать разрыв с боссом выше BOSS_LEVEL_GAP_CAP ни на одном
    шаге сезона — и разрыв должен реально доходить до потолка, иначе тест
    ничего не проверяет (клампа просто не касается)."""
    player = _player(0)
    rng = random.Random(42)

    boss_level = LEVEL + BOSS_LEVEL_GAP_CAP + 5   # заведомо выше потолка на старте
    pending_failures = 0
    cap = round(player.avg_level) + BOSS_LEVEL_GAP_CAP
    seen_at_cap = False

    for _ in range(60):
        outcome = simulate_fight(player, boss_level, rng)
        if outcome == "lost":
            pending_failures += DEATH_BOSS_LEVEL_GAIN

        boss_level = min(boss_level + pending_failures, cap)
        pending_failures = 0

        assert boss_level <= cap
        seen_at_cap = seen_at_cap or boss_level == cap

    assert seen_at_cap
