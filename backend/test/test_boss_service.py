import pytest
from datetime import date, datetime, timezone, timedelta
from fastapi import HTTPException
import datetime as datetime_module
from app.models.user import User
from app.models.stat import Stat, CombatRole
from app.models.boss import Boss
from app.models.quest import Quest, QuestType, QuestStatus
from app.core.auth import hash_password
from app.core.constant import BASE_MAX_HP, HP_PER_HEALTH_LEVEL, BOSS_BASE_HP, BOSS_HP_PER_LEVEL, HEAL_COST
from app.service.boss import fight_boss, get_boss_status, heal, calculate_max_hp, calculate_boss_hp


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


def test_calculate_boss_hp():
    assert calculate_boss_hp(1) == BOSS_BASE_HP + BOSS_HP_PER_LEVEL


async def test_fight_before_window_rejected(db_session, user_with_boss, monkeypatch):
    import app.service.boss as boss_module

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)  # раньше 17:00

    monkeypatch.setattr(boss_module, "datetime", FakeDatetime)

    with pytest.raises(HTTPException) as exc_info:
        await fight_boss(db_session, user_with_boss.id)
    assert exc_info.value.status_code == 400


async def test_fight_win_awards_currency_and_xp(db_session, user_with_boss, monkeypatch):
    import app.service.boss as boss_module

    real_datetime = datetime_module.datetime

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            actual = real_datetime.now(tz)
            return actual.replace(hour=18, minute=0, second=0, microsecond=0)  # в окне боя

    monkeypatch.setattr(boss_module, "datetime", FakeDatetime)

    stats_result = await db_session.execute(
        Stat.__table__.select().where(Stat.user_id == user_with_boss.id)
    )
    stat_rows = stats_result.fetchall()
    stat_ids = {row.name: row.id for row in stat_rows}

    # прокачаем силу, чтобы гарантированно хватило урона
    strength_stat = await db_session.get(Stat, stat_ids["Сила"])
    strength_stat.level = 200
    await db_session.flush()

    await _complete_quest_with_stat(db_session, user_with_boss.id, stat_ids["Сила"])
    await _complete_quest_with_stat(db_session, user_with_boss.id, stat_ids["Ловкость"])
    await db_session.commit()

    fight = await fight_boss(db_session, user_with_boss.id)

    assert fight.result == "won"
    await db_session.refresh(user_with_boss)
    assert user_with_boss.boss_currency_balance > 0


async def test_fight_loss_reduces_hp(db_session, user_with_boss, monkeypatch):
    import app.service.boss as boss_module

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(boss_module, "datetime", FakeDatetime)

    # никаких выполненных квестов -> distinct_stats = 0 -> damage_dealt = 0 -> гарантированное поражение
    fight = await fight_boss(db_session, user_with_boss.id)

    assert fight.result == "lost"
    await db_session.refresh(user_with_boss)
    assert user_with_boss.current_hp < BASE_MAX_HP + HP_PER_HEALTH_LEVEL


async def test_cannot_fight_twice_same_day(db_session, user_with_boss, monkeypatch):
    import app.service.boss as boss_module

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(boss_module, "datetime", FakeDatetime)

    await fight_boss(db_session, user_with_boss.id)

    with pytest.raises(HTTPException) as exc_info:
        await fight_boss(db_session, user_with_boss.id)
    assert exc_info.value.status_code == 400


async def test_heal_restores_hp_and_costs_currency(db_session, user_with_boss):
    user_with_boss.current_hp = 0
    user_with_boss.boss_currency_balance = HEAL_COST
    await db_session.commit()

    result = await heal(db_session, user_with_boss.id)

    assert result.current_hp > 0
    assert result.boss_currency_balance == 0


async def test_heal_insufficient_currency_fails(db_session, user_with_boss):
    user_with_boss.boss_currency_balance = 0
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await heal(db_session, user_with_boss.id)
    assert exc_info.value.status_code == 400
