import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy import select
from app.models.user import User
from app.models.stat import Stat, CombatRole
from app.models.boss import Boss
from app.models.quest import Quest, QuestType, QuestStatus
from app.core.auth import hash_password, create_access_token
from app.core.constant import (
    BASE_MAX_HP, HP_PER_HEALTH_LEVEL, COUNT_ROUND, BOSS_TARGET_KILL_ROUNDS,
    BOSS_KILL_ROUNDS_SLACKER, BOSS_HP_REFERENCE_EFFORT, QUEST_EFFORT_CAP,
)
from app.core.constant import CRIT_MULTIPLIER
from app.core.constant_shop import (
    HEAL_COST, SPEC_STRENGTH_ATTACK_MULTIPLIER, SPEC_FOCUS_ACCURACY_MULTIPLIER,
    SPEC_AGILITY_EVASION_MULTIPLIER, SPEC_INTELLECT_CRIT_BONUS,
    EYE_FOCUS_CRIT_MULTIPLIER, SPEC_HEALTH_REGEN_BONUS,
)
from app.service.boss import (
    get_boss_status, heal, calculate_max_hp, calculate_boss_hp,
    invalidate_boss_status, ensure_hp_regen, load_combat_profile,
)
from app.service.combat import (
    build_player_combat, calculate_boss_attack, expected_damage_per_round,
    hit_chance_on_player,
)
from app.service.inventory import grant_charge


@pytest.fixture
async def user_with_boss(db_session):
    u = User(username="fighter", email="fighter@test.com", password_hash=hash_password("password123"))
    db_session.add(u)
    await db_session.flush()

    stats = {
        "Сила": CombatRole.strength,
        "Ловкость": CombatRole.agility,
        "Интелект": CombatRole.intellect,
        "Фокус": CombatRole.focus,
        "Здоровье": CombatRole.health,
    }
    for name, role in stats.items():
        db_session.add(Stat(user_id=u.id, name=name, combat_role=role, is_default=True, level=1))

    db_session.add(Boss(user_id=u.id, level=1, pending_failures=0))
    await db_session.flush()
    return u


async def _complete_quest_with_stat(db_session, user_id, stat_id):
    quest = Quest(
        user_id=user_id,
        stat_id=stat_id,
        name="test quest",
        quest_type=QuestType.once,
        status=QuestStatus.done,
        last_completed_at=datetime.now(timezone.utc),
    )
    db_session.add(quest)
    await db_session.flush()
    return quest


def test_calculate_max_hp():
    assert calculate_max_hp(0) == BASE_MAX_HP
    assert calculate_max_hp(1) == BASE_MAX_HP + HP_PER_HEALTH_LEVEL


def test_boss_hp_grows_with_levels():
    """HP босса растёт и от уровня игрока, и от уровня самого босса."""
    assert calculate_boss_hp(5, 5) > calculate_boss_hp(3, 3)
    assert calculate_boss_hp(5, 8) > calculate_boss_hp(5, 5)
    assert calculate_boss_hp(1, 1) >= 1


def test_boss_hp_calibrated_to_target_rounds():
    """Эталонный игрок (типичный день) должен убивать босса своего уровня
    примерно за BOSS_TARGET_KILL_ROUNDS раундов — иначе лимит в 7 раундов
    перестаёт что-либо значить."""
    level = 6
    quests = round(BOSS_HP_REFERENCE_EFFORT * QUEST_EFFORT_CAP)
    player = build_player_combat(
        {role: level for role in CombatRole},
        {role: quests for role in CombatRole},
    )
    rounds = calculate_boss_hp(player.avg_level, level) / expected_damage_per_round(player, level)
    assert BOSS_TARGET_KILL_ROUNDS - 1 <= rounds <= BOSS_TARGET_KILL_ROUNDS + 1
    assert rounds <= COUNT_ROUND


def test_slacker_dies_on_schedule():
    """Игрок без единого квеста должен ложиться примерно на BOSS_KILL_ROUNDS_SLACKER."""
    level = 6
    player = build_player_combat({role: level for role in CombatRole}, {})
    boss_dps = calculate_boss_attack(player.max_hp, player.diligence) * hit_chance_on_player(
        player.evasion, level
    )
    rounds = player.max_hp / boss_dps
    assert rounds < COUNT_ROUND
    assert abs(rounds - BOSS_KILL_ROUNDS_SLACKER) <= 1.5


def test_quests_and_evasion_are_not_self_cancelling():
    """Ключевая ловушка модели: если HP/урон босса считать от ФАКТИЧЕСКИХ
    точности и уклонения игрока, прокачка обнуляет сама себя."""
    level = 6
    lazy = build_player_combat({role: level for role in CombatRole}, {})
    busy = build_player_combat(
        {role: level for role in CombatRole},
        {role: QUEST_EFFORT_CAP for role in CombatRole},
    )
    # одинаковый уровень -> одинаковый босс, но разный результат
    assert calculate_boss_hp(lazy.avg_level, level) == calculate_boss_hp(busy.avg_level, level)
    assert expected_damage_per_round(busy, level) > expected_damage_per_round(lazy, level)
    # уклонение реально снижает входящий урон, а не компенсируется уроном за удар
    assert hit_chance_on_player(busy.evasion, level) < hit_chance_on_player(lazy.evasion, level)


async def test_heal_restores_hp_and_costs_currency(db_session, user_with_boss, fake_redis):
    user_with_boss.current_hp = 0
    user_with_boss.boss_currency_balance = HEAL_COST
    await db_session.commit()

    result = await heal(db_session, user_with_boss.id, fake_redis)

    assert result.current_hp > 0
    assert result.boss_currency_balance == 0


async def test_heal_insufficient_currency_fails(db_session, user_with_boss, fake_redis):
    user_with_boss.boss_currency_balance = 0
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await heal(db_session, user_with_boss.id, fake_redis)
    assert exc_info.value.status_code == 400


async def test_boss_status_endpoint_works_end_to_end(client, db_session, user_with_boss):
    """Проходит весь путь: роутер -> авторизация -> сервис -> кэш.

    Redis здесь подменён FakeRedis, так что поломки НАСТОЯЩЕГО клиента этот
    тест не поймает — за это отвечает test_redis_client.py.
    """
    await db_session.commit()
    token = create_access_token(data={"sub": str(user_with_boss.id)})

    response = await client.get("/boss/status", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["boss_level"] == 1
    assert data["boss_hp"] > 0


async def test_boss_status_is_cached_and_invalidated(client, db_session, user_with_boss, fake_redis):
    """Второй запрос должен прийти из кэша, а heal — кэш сбросить."""
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(data={"sub": str(user_with_boss.id)})}"}

    await client.get("/boss/status", headers=headers)
    assert len(fake_redis._data) == 1        # статус лёг в кэш

    await invalidate_boss_status(fake_redis, user_with_boss.id)
    assert len(fake_redis._data) == 0        # инвалидация действительно чистит


# ────────────────── Постоянные предметы (artifacts/shop-design.md) ──────────────────

def test_spec_items_boost_matching_stats_only():
    level = 6
    base = build_player_combat({role: level for role in CombatRole}, {})

    strength = build_player_combat({role: level for role in CombatRole}, {}, frozenset({"spec_strength"}))
    assert strength.attack == pytest.approx(base.attack * SPEC_STRENGTH_ATTACK_MULTIPLIER)
    assert strength.accuracy == base.accuracy and strength.evasion == base.evasion

    focus = build_player_combat({role: level for role in CombatRole}, {}, frozenset({"spec_focus"}))
    assert focus.accuracy == pytest.approx(base.accuracy * SPEC_FOCUS_ACCURACY_MULTIPLIER)

    agility = build_player_combat({role: level for role in CombatRole}, {}, frozenset({"spec_agility"}))
    assert agility.evasion == pytest.approx(base.evasion * SPEC_AGILITY_EVASION_MULTIPLIER)

    intellect = build_player_combat({role: level for role in CombatRole}, {}, frozenset({"spec_intellect"}))
    assert intellect.crit_chance == pytest.approx(base.crit_chance + SPEC_INTELLECT_CRIT_BONUS)


def test_eye_focus_changes_crit_multiplier_not_boss_hp_reference():
    """eye_focus должен усиливать только фактический урон игрока. Если бы он
    протекал в calculate_boss_hp (эталон), прокачка обнулила бы сама себя —
    тот же класс бага, что стережёт test_quests_and_evasion_are_not_self_cancelling."""
    level = 6
    without = build_player_combat({role: level for role in CombatRole}, {})
    with_item = build_player_combat({role: level for role in CombatRole}, {}, frozenset({"eye_focus"}))

    assert without.crit_multiplier == CRIT_MULTIPLIER
    assert with_item.crit_multiplier == EYE_FOCUS_CRIT_MULTIPLIER
    # HP босса считается от avg_level, а не от crit_multiplier — эталон не сдвинулся
    assert calculate_boss_hp(without.avg_level, level) == calculate_boss_hp(with_item.avg_level, level)


async def test_load_combat_profile_picks_up_owned_specializations(db_session, user_with_boss):
    await grant_charge(db_session, user_with_boss.id, "spec_strength")
    await db_session.commit()

    today = datetime.now(timezone.utc).date()
    without = build_player_combat({role: 1 for role in CombatRole}, {})
    profile = await load_combat_profile(db_session, user_with_boss.id, today, ZoneInfo("UTC"))

    assert profile.attack == pytest.approx(without.attack * SPEC_STRENGTH_ATTACK_MULTIPLIER)


async def test_spec_health_boosts_daily_regen(db_session, user_with_boss, fake_redis):
    plain_user = User(username="noregen", email="noregen@test.com", password_hash=hash_password("password123"))
    db_session.add(plain_user)
    await db_session.flush()
    for name, role in {
        "Сила": CombatRole.strength, "Ловкость": CombatRole.agility,
        "Интелект": CombatRole.intellect, "Фокус": CombatRole.focus,
        "Здоровье": CombatRole.health,
    }.items():
        db_session.add(Stat(user_id=plain_user.id, name=name, combat_role=role, is_default=True, level=1))

    await grant_charge(db_session, user_with_boss.id, "spec_health")

    for user in (user_with_boss, plain_user):
        user.current_hp = 0
        user.hp_regen_date = None
    await db_session.commit()

    await ensure_hp_regen(db_session, user_with_boss.id)
    await ensure_hp_regen(db_session, plain_user.id)

    await db_session.refresh(user_with_boss)
    await db_session.refresh(plain_user)
    assert user_with_boss.current_hp > plain_user.current_hp


# ────────────────── Мультистат-квесты в боевом профиле ──────────────────

async def test_load_combat_profile_counts_quest_for_both_attached_stats(db_session, user_with_boss):
    """Квест с двумя статами (stat_id + stat_id_2) должен засчитаться в effort
    обоих — иначе второй слот квеста никак не влиял бы на бой."""
    stats = (await db_session.execute(
        select(Stat).where(Stat.user_id == user_with_boss.id).order_by(Stat.id)
    )).scalars().all()
    strength = next(s for s in stats if s.combat_role == CombatRole.strength)
    health = next(s for s in stats if s.combat_role == CombatRole.health)

    db_session.add(Quest(
        user_id=user_with_boss.id,
        stat_id=strength.id,
        stat_id_2=health.id,
        name="зал",
        quest_type=QuestType.once,
        status=QuestStatus.done,
        last_completed_at=datetime.now(timezone.utc),
    ))
    await db_session.flush()

    today = datetime.now(timezone.utc).date()
    profile = await load_combat_profile(db_session, user_with_boss.id, today, ZoneInfo("UTC"))

    expected = build_player_combat(
        {role: 1 for role in CombatRole},
        {CombatRole.strength: 1, CombatRole.health: 1},
    )
    assert profile.attack == pytest.approx(expected.attack)
    assert profile.max_hp == pytest.approx(expected.max_hp)


async def test_load_combat_profile_counts_two_quests_on_same_stat_separately(db_session, user_with_boss):
    """union_all, не union: две РАЗНЫЕ привычки на одну и ту же силу должны
    засчитаться как 2 квеста effort'а, а не схлопнуться в одну строку."""
    stats = (await db_session.execute(
        select(Stat).where(Stat.user_id == user_with_boss.id).order_by(Stat.id)
    )).scalars().all()
    strength = next(s for s in stats if s.combat_role == CombatRole.strength)

    for name in ("квест 1", "квест 2"):
        db_session.add(Quest(
            user_id=user_with_boss.id,
            stat_id=strength.id,
            name=name,
            quest_type=QuestType.once,
            status=QuestStatus.done,
            last_completed_at=datetime.now(timezone.utc),
        ))
    await db_session.flush()

    today = datetime.now(timezone.utc).date()
    profile = await load_combat_profile(db_session, user_with_boss.id, today, ZoneInfo("UTC"))

    expected = build_player_combat({role: 1 for role in CombatRole}, {CombatRole.strength: 2})
    assert profile.attack == pytest.approx(expected.attack)
