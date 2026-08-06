import pytest
from datetime import date, datetime, timezone, timedelta
from fastapi import HTTPException
import datetime as datetime_module
from app.models.user import User
from app.models.stat import Stat, CombatRole
from app.models.boss import Boss
from app.models.quest import Quest, QuestType, QuestStatus
from app.core.auth import hash_password, create_access_token
from app.core.constant import (
    BASE_MAX_HP, HP_PER_HEALTH_LEVEL, COUNT_ROUND, BOSS_TARGET_KILL_ROUNDS,
    BOSS_KILL_ROUNDS_SLACKER, BOSS_HP_REFERENCE_EFFORT, QUEST_EFFORT_CAP,
)
from app.core.constant_shop import HEAL_COST
from app.service.boss import (
    get_boss_status, heal, calculate_max_hp, calculate_boss_hp,
    invalidate_boss_status,
)
from app.service.combat import (
    build_player_combat, calculate_boss_attack, expected_damage_per_round,
    hit_chance_on_player,
)


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
