from datetime import datetime, timezone

import pytest

from app.core.auth import hash_password
from app.models.quest import Quest, QuestStatus, QuestType
from app.models.user import User
from app.service import reminders as reminders_module
from app.service.reminders import send_due_habit_reminders


@pytest.fixture
async def user(db_session):
    u = User(
        username="tg-tester",
        email="tg-tester@test.com",
        password_hash=hash_password("password123"),
        telegram_chat_id=123456,
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.fixture
def sent_messages(monkeypatch):
    calls = []

    async def fake_send_message(chat_id, text):
        calls.append((chat_id, text))
        return True

    monkeypatch.setattr(reminders_module, "send_message", fake_send_message)
    return calls


def _habit(user, **overrides):
    defaults = dict(
        user_id=user.id,
        name="зал",
        quest_type=QuestType.habit,
        status=QuestStatus.active,
        scheduled_days=[0, 2, 4],  # пн/ср/пт
        reminder_times={"0": "08:00", "2": "08:00", "4": "08:00"},
    )
    defaults.update(overrides)
    return Quest(**defaults)


async def test_sends_reminder_when_due(db_session, user, sent_messages, session_factory, freeze_time):
    quest = _habit(user)
    db_session.add(quest)
    await db_session.commit()

    freeze_time(datetime(2026, 8, 3, 8, 5, tzinfo=timezone.utc))  # понедельник, 08:05 — время настало

    await send_due_habit_reminders(session_factory)

    assert sent_messages == [(123456, '⏰ «зал» — время для привычки!')]
    await db_session.refresh(quest)
    assert quest.last_notified_date == datetime(2026, 8, 3).date()


async def test_skips_before_reminder_time(db_session, user, sent_messages, session_factory, freeze_time):
    quest = _habit(user)
    db_session.add(quest)
    await db_session.commit()

    freeze_time(datetime(2026, 8, 3, 7, 55, tzinfo=timezone.utc))  # ещё раньше 08:00

    await send_due_habit_reminders(session_factory)

    assert sent_messages == []
    await db_session.refresh(quest)
    assert quest.last_notified_date is None


async def test_skips_when_already_completed_today(db_session, user, sent_messages, session_factory, freeze_time):
    quest = _habit(user, last_completed_at=datetime(2026, 8, 3, 7, 0, tzinfo=timezone.utc))
    db_session.add(quest)
    await db_session.commit()

    freeze_time(datetime(2026, 8, 3, 8, 5, tzinfo=timezone.utc))

    await send_due_habit_reminders(session_factory)

    assert sent_messages == []


async def test_does_not_resend_same_day(db_session, user, sent_messages, session_factory, freeze_time):
    quest = _habit(user, last_notified_date=datetime(2026, 8, 3).date())
    db_session.add(quest)
    await db_session.commit()

    freeze_time(datetime(2026, 8, 3, 8, 5, tzinfo=timezone.utc))

    await send_due_habit_reminders(session_factory)

    assert sent_messages == []


async def test_skips_without_telegram_chat_id(db_session, session_factory, sent_messages, freeze_time):
    u = User(username="no-tg", email="no-tg@test.com", password_hash=hash_password("password123"))
    db_session.add(u)
    await db_session.flush()
    quest = _habit(u)
    db_session.add(quest)
    await db_session.commit()

    freeze_time(datetime(2026, 8, 3, 8, 5, tzinfo=timezone.utc))

    await send_due_habit_reminders(session_factory)

    assert sent_messages == []


async def test_skips_when_no_reminder_for_todays_weekday(db_session, user, sent_messages, session_factory, freeze_time):
    quest = _habit(user, reminder_times={"0": "08:00"})  # только понедельник
    db_session.add(quest)
    await db_session.commit()

    freeze_time(datetime(2026, 8, 4, 8, 5, tzinfo=timezone.utc))  # вторник

    await send_due_habit_reminders(session_factory)

    assert sent_messages == []
