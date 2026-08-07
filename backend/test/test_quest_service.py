import pytest
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select

from app.models.user import User
from app.models.quest import Quest, QuestType, QuestStatus
from app.models.stat import Stat
from app.models.boss import Boss
from app.core.auth import hash_password
from app.core.constant import OFF_SCHEDULE_HP_PENALTY, STREAK_LOOKBACK_DAYS
from app.service import quest as quest_module
from app.service.quest import (
    complete_quest,
    refresh_recurring_quests,
    mark_overdue_quest_failed,
    process_scheduled_habits,
)
from fastapi import HTTPException


@pytest.fixture
async def user(db_session):
    u = User(username="tester", email="tester@test.com", password_hash=hash_password("password123"))
    db_session.add(u)
    await db_session.flush()
    return u


async def test_complete_quest_awards_currency(db_session, user):
    quest = Quest(user_id=user.id, name="q1", reward_currency=15, reward_xp=0, quest_type=QuestType.once)
    db_session.add(quest)
    await db_session.flush()

    result = await complete_quest(db_session, user.id, quest.id)

    assert result.status == QuestStatus.done
    await db_session.refresh(user)
    assert user.currency_balance == 15


async def test_complete_quest_awards_xp_to_stat(db_session, user):
    stat = Stat(user_id=user.id, name="Сила", xp_to_next_level=100)
    db_session.add(stat)
    await db_session.flush()

    quest = Quest(user_id=user.id, stat_id=stat.id, name="q2", reward_currency=0, reward_xp=30, quest_type=QuestType.once)
    db_session.add(quest)
    await db_session.flush()

    await complete_quest(db_session, user.id, quest.id)

    await db_session.refresh(stat)
    assert stat.current_xp == 30
    assert stat.level == 1


async def test_complete_quest_multiple_level_ups(db_session, user):
    stat = Stat(user_id=user.id, name="Ловкость", xp_to_next_level=10, level=1)
    db_session.add(stat)
    await db_session.flush()

    # reward_xp хватит на несколько level-up при пороге 10 (10 -> 15 -> 22...)
    quest = Quest(user_id=user.id, stat_id=stat.id, name="q3", reward_currency=0, reward_xp=35, quest_type=QuestType.once)
    db_session.add(quest)
    await db_session.flush()

    await complete_quest(db_session, user.id, quest.id)

    await db_session.refresh(stat)
    assert stat.level > 1


async def test_cannot_complete_quest_twice(db_session, user):
    quest = Quest(user_id=user.id, name="q4", quest_type=QuestType.once)
    db_session.add(quest)
    await db_session.flush()

    await complete_quest(db_session, user.id, quest.id)

    with pytest.raises(HTTPException) as exc_info:
        await complete_quest(db_session, user.id, quest.id)
    assert exc_info.value.status_code == 400


async def test_complete_nonexistent_quest_returns_404(db_session, user):
    with pytest.raises(HTTPException) as exc_info:
        await complete_quest(db_session, user.id, 99999)
    assert exc_info.value.status_code == 404


async def test_complete_other_users_quest_returns_404(db_session, user):
    other_user = User(username="other", email="other@test.com", password_hash=hash_password("password123"))
    db_session.add(other_user)
    await db_session.flush()

    quest = Quest(user_id=other_user.id, name="not yours", quest_type=QuestType.once)
    db_session.add(quest)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await complete_quest(db_session, user.id, quest.id)
    assert exc_info.value.status_code == 404


async def test_habit_quest_stays_active_after_completion(db_session, user):
    quest = Quest(user_id=user.id, name="habit q", quest_type=QuestType.habit)
    db_session.add(quest)
    await db_session.flush()

    result = await complete_quest(db_session, user.id, quest.id)

    assert result.status == QuestStatus.active


async def test_daily_quest_resets_after_calendar_day(db_session, user):
    quest = Quest(
        user_id=user.id,
        name="daily q",
        quest_type=QuestType.daily,
        status=QuestStatus.done,
        last_completed_at=datetime.now(timezone.utc) - timedelta(days=1, hours=1),
    )
    db_session.add(quest)
    await db_session.flush()

    await refresh_recurring_quests(db_session, user.id)

    await db_session.refresh(quest)
    assert quest.status == QuestStatus.active


async def test_daily_quest_stays_done_same_day(db_session, user):
    quest = Quest(
        user_id=user.id,
        name="daily q2",
        quest_type=QuestType.daily,
        status=QuestStatus.done,
        last_completed_at=datetime.now(timezone.utc),
    )
    db_session.add(quest)
    await db_session.flush()

    await refresh_recurring_quests(db_session, user.id)

    await db_session.refresh(quest)
    assert quest.status == QuestStatus.done


async def test_overdue_quest_marked_failed(db_session, user):
    quest = Quest(
        user_id=user.id,
        name="overdue q",
        quest_type=QuestType.once,
        status=QuestStatus.active,
        date_end=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(quest)
    await db_session.flush()

    await mark_overdue_quest_failed(db_session, user.id)

    await db_session.refresh(quest)
    assert quest.status == QuestStatus.failed


async def test_quest_without_deadline_not_touched(db_session, user):
    quest = Quest(user_id=user.id, name="no deadline", quest_type=QuestType.once, status=QuestStatus.active, date_end=None)
    db_session.add(quest)
    await db_session.flush()

    await mark_overdue_quest_failed(db_session, user.id)

    await db_session.refresh(quest)
    assert quest.status == QuestStatus.active


async def test_complete_quest_splits_xp_between_two_stats(db_session, user):
    stat_a = Stat(user_id=user.id, name="Сила", xp_to_next_level=100)
    stat_b = Stat(user_id=user.id, name="Здоровье", xp_to_next_level=100)
    db_session.add_all([stat_a, stat_b])
    await db_session.flush()

    quest = Quest(
        user_id=user.id,
        stat_id=stat_a.id,
        stat_id_2=stat_b.id,
        name="зал",
        reward_currency=0,
        reward_xp=40,
        quest_type=QuestType.once,
    )
    db_session.add(quest)
    await db_session.flush()

    await complete_quest(db_session, user.id, quest.id)

    await db_session.refresh(stat_a)
    await db_session.refresh(stat_b)
    assert stat_a.current_xp == 20
    assert stat_b.current_xp == 20


async def test_scheduled_habit_cannot_complete_twice_same_day(db_session, user, monkeypatch):
    quest = Quest(
        user_id=user.id,
        name="зал пн/ср/пт",
        quest_type=QuestType.habit,
        scheduled_days=[0, 2, 4],
        date_start=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc),  # понедельник
    )
    db_session.add(quest)
    await db_session.flush()

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(quest_module, "datetime", FakeDatetime)

    await complete_quest(db_session, user.id, quest.id)

    with pytest.raises(HTTPException) as exc_info:
        await complete_quest(db_session, user.id, quest.id)
    assert exc_info.value.status_code == 400


async def test_scheduled_habit_streak_increments_without_gap(db_session, user, monkeypatch):
    quest = Quest(
        user_id=user.id,
        name="зал",
        quest_type=QuestType.habit,
        scheduled_days=[0, 2, 4],  # пн/ср/пт
        date_start=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc),
        last_completed_at=datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc),  # выполнено в пн
        current_streak=1,
        streak_checked_until=date(2026, 8, 3),
    )
    db_session.add(quest)
    await db_session.flush()

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 5, 9, 0, tzinfo=timezone.utc)  # среда — следующий день по расписанию

    monkeypatch.setattr(quest_module, "datetime", FakeDatetime)

    result = await complete_quest(db_session, user.id, quest.id)

    assert result.current_streak == 2
    assert result.best_streak == 2


async def test_scheduled_habit_streak_resets_and_penalizes_boss_on_missed_day(db_session, user, monkeypatch):
    db_session.add(Boss(user_id=user.id, level=1, pending_failures=0))

    quest = Quest(
        user_id=user.id,
        name="зал",
        quest_type=QuestType.habit,
        scheduled_days=[0, 2, 4],  # пн/ср/пт
        date_start=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc),
        last_completed_at=datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc),  # выполнено в пн
        current_streak=1,
        best_streak=1,
        streak_checked_until=date(2026, 8, 3),
    )
    db_session.add(quest)
    await db_session.flush()

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc)  # пятница — среда пропущена

    monkeypatch.setattr(quest_module, "datetime", FakeDatetime)

    result = await complete_quest(db_session, user.id, quest.id)

    assert result.current_streak == 1  # серия начата заново

    boss_result = await db_session.execute(select(Boss).where(Boss.user_id == user.id))
    boss = boss_result.scalar_one()
    assert boss.pending_failures == 1


async def test_process_scheduled_habits_penalizes_missed_day_lazily(db_session, user, monkeypatch):
    db_session.add(Boss(user_id=user.id, level=1, pending_failures=0))

    quest = Quest(
        user_id=user.id,
        name="зал",
        quest_type=QuestType.habit,
        scheduled_days=[0, 2, 4],  # пн/ср/пт
        date_start=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc),
        last_completed_at=datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc),  # выполнено в пн
        current_streak=1,
        streak_checked_until=date(2026, 8, 3),
    )
    db_session.add(quest)
    await db_session.flush()

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 6, 9, 0, tzinfo=timezone.utc)  # четверг: среда уже прошла без выполнения

    monkeypatch.setattr(quest_module, "datetime", FakeDatetime)

    await process_scheduled_habits(db_session, user.id)

    await db_session.refresh(quest)
    assert quest.current_streak == 0

    boss_result = await db_session.execute(select(Boss).where(Boss.user_id == user.id))
    boss = boss_result.scalar_one()
    assert boss.pending_failures == 1


async def test_missed_days_are_capped_by_lookback_window(db_session, user, monkeypatch):
    """Привычка, у которой streak_checked_until пуст (расписание проставили позже),
    не должна обвалить на пользователя штраф за всю её историю."""
    db_session.add(Boss(user_id=user.id, level=1, pending_failures=0))

    quest = Quest(
        user_id=user.id,
        name="старая привычка",
        quest_type=QuestType.habit,
        scheduled_days=[0, 1, 2, 3, 4, 5, 6],  # каждый день
        date_start=datetime(2025, 8, 7, 8, 0, tzinfo=timezone.utc),  # год назад
        streak_checked_until=None,
    )
    db_session.add(quest)
    await db_session.flush()

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(quest_module, "datetime", FakeDatetime)

    await process_scheduled_habits(db_session, user.id)

    boss_result = await db_session.execute(select(Boss).where(Boss.user_id == user.id))
    boss = boss_result.scalar_one()
    assert boss.pending_failures == STREAK_LOOKBACK_DAYS


async def test_failed_habit_does_not_keep_penalizing_boss(db_session, user, monkeypatch):
    """Привычку с истёкшим date_end mark_overdue_quest_failed уже наказала один раз —
    дальше она не должна бить по боссу за каждый день расписания."""
    db_session.add(Boss(user_id=user.id, level=1, pending_failures=0))

    quest = Quest(
        user_id=user.id,
        name="заброшенная привычка",
        quest_type=QuestType.habit,
        scheduled_days=[0, 1, 2, 3, 4, 5, 6],
        status=QuestStatus.failed,
        date_start=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc),
        streak_checked_until=date(2026, 8, 3),
    )
    db_session.add(quest)
    await db_session.flush()

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(quest_module, "datetime", FakeDatetime)

    await process_scheduled_habits(db_session, user.id)

    boss_result = await db_session.execute(select(Boss).where(Boss.user_id == user.id))
    boss = boss_result.scalar_one()
    assert boss.pending_failures == 0


async def test_off_schedule_completion_costs_hp(db_session, user, monkeypatch):
    """Внеплановое выполнение засчитывается в серию, но снимает HP —
    иначе привычку «только по понедельникам» можно накручивать каждый день."""
    user.current_hp = 100
    quest = Quest(
        user_id=user.id,
        name="зал по понедельникам",
        quest_type=QuestType.habit,
        scheduled_days=[0],
        date_start=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc),  # понедельник
        streak_checked_until=date(2026, 8, 3),
    )
    db_session.add(quest)
    await db_session.flush()

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 4, 9, 0, tzinfo=timezone.utc)  # вторник — не по расписанию

    monkeypatch.setattr(quest_module, "datetime", FakeDatetime)

    result = await complete_quest(db_session, user.id, quest.id)

    assert result.current_streak == 1
    await db_session.refresh(user)
    assert user.current_hp == 100 - OFF_SCHEDULE_HP_PENALTY


async def test_on_schedule_completion_does_not_cost_hp(db_session, user, monkeypatch):
    user.current_hp = 100
    quest = Quest(
        user_id=user.id,
        name="зал по понедельникам",
        quest_type=QuestType.habit,
        scheduled_days=[0],
        date_start=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc),
    )
    db_session.add(quest)
    await db_session.flush()

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)  # понедельник

    monkeypatch.setattr(quest_module, "datetime", FakeDatetime)

    await complete_quest(db_session, user.id, quest.id)

    await db_session.refresh(user)
    assert user.current_hp == 100


async def test_get_then_complete_same_day_penalizes_once(db_session, user, monkeypatch):
    """Роутер зовёт process_scheduled_habits перед выдачей списка, а затем
    пользователь жмёт «Выполнить» — один пропуск не должен посчитаться дважды."""
    db_session.add(Boss(user_id=user.id, level=1, pending_failures=0))

    quest = Quest(
        user_id=user.id,
        name="зал",
        quest_type=QuestType.habit,
        scheduled_days=[0, 2, 4],  # пн/ср/пт
        date_start=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc),
        last_completed_at=datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc),
        current_streak=1,
        streak_checked_until=date(2026, 8, 3),
    )
    db_session.add(quest)
    await db_session.flush()

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc)  # пятница, среда пропущена

    monkeypatch.setattr(quest_module, "datetime", FakeDatetime)

    await process_scheduled_habits(db_session, user.id)
    await complete_quest(db_session, user.id, quest.id)

    boss_result = await db_session.execute(select(Boss).where(Boss.user_id == user.id))
    boss = boss_result.scalar_one()
    assert boss.pending_failures == 1

