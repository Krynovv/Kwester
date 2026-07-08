import pytest
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.models.quest import Quest, QuestType, QuestStatus
from app.models.stat import Stat
from app.core.auth import hash_password
from app.service.quest import complete_quest, refresh_recurring_quests, mark_overdue_quest_failed
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
