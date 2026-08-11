import pytest
from datetime import datetime, timezone
from sqlalchemy import select

from app.models.quest import Quest, QuestType


@pytest.fixture
async def auth_headers(client):
    await client.post("/auth/register", json={
        "username": "questapi",
        "email": "questapi@test.com",
        "password": "password123",
    })
    response = await client.post("/auth/token", data={
        "username": "questapi",
        "password": "password123",
    })
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_create_scheduled_habit_marks_schedule_checked(client, auth_headers, db_session):
    """streak_checked_until должен проставляться сразу, иначе первый же GET
    насчитает пропуски начиная с date_start."""
    response = await client.post("/quest", headers=auth_headers, json={
        "name": "зал",
        "quest_type": "habit",
        "scheduled_days": [0, 2, 4],
    })
    assert response.status_code == 201

    quest = (await db_session.execute(
        select(Quest).where(Quest.id == response.json()["id"])
    )).scalar_one()
    assert quest.streak_checked_until == datetime.now(timezone.utc).date()


async def test_adding_schedule_later_resets_streak_window(client, auth_headers, db_session):
    """Привычка без расписания живёт с date_start в прошлом. Когда расписание
    добавляют через PATCH, окно проверки пропусков должно начаться с сегодня."""
    created = await client.post("/quest", headers=auth_headers, json={
        "name": "старая привычка",
        "quest_type": "habit",
    })
    quest_id = created.json()["id"]

    quest = (await db_session.execute(select(Quest).where(Quest.id == quest_id))).scalar_one()
    quest.date_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    quest.current_streak = 7
    await db_session.commit()

    response = await client.patch(f"/quest/{quest_id}", headers=auth_headers, json={
        "scheduled_days": [0, 1, 2, 3, 4, 5, 6],
    })
    assert response.status_code == 200

    await db_session.refresh(quest)
    assert quest.streak_checked_until == datetime.now(timezone.utc).date()
    assert quest.current_streak == 0


async def test_clearing_schedule_clears_checked_until(client, auth_headers, db_session):
    created = await client.post("/quest", headers=auth_headers, json={
        "name": "зал",
        "quest_type": "habit",
        "scheduled_days": [0, 2, 4],
    })
    quest_id = created.json()["id"]

    response = await client.patch(f"/quest/{quest_id}", headers=auth_headers, json={
        "scheduled_days": None,
    })
    assert response.status_code == 200

    quest = (await db_session.execute(select(Quest).where(Quest.id == quest_id))).scalar_one()
    await db_session.refresh(quest)
    assert quest.scheduled_days is None
    assert quest.streak_checked_until is None


async def test_quest_read_exposes_last_completed_at(client, auth_headers):
    """Без этого поля QuestCard не может погасить «Выполнить» у привычки,
    уже закрытой сегодня, и пользователь ловит 400 по нажатию."""
    created = await client.post("/quest", headers=auth_headers, json={
        "name": "зал",
        "quest_type": "habit",
        "scheduled_days": [0, 1, 2, 3, 4, 5, 6],
    })
    quest_id = created.json()["id"]
    assert created.json()["last_completed_at"] is None

    completed = await client.post(f"/quest/{quest_id}/complete", headers=auth_headers)
    assert completed.json()["last_completed_at"] is not None


async def test_schedule_rejected_for_non_habit(client, auth_headers):
    response = await client.post("/quest", headers=auth_headers, json={
        "name": "разовый",
        "quest_type": "once",
        "scheduled_days": [0],
    })
    assert response.status_code == 422


async def test_duplicate_stats_rejected_on_create(client, auth_headers, db_session):
    from app.models.stat import Stat

    stat = (await db_session.execute(select(Stat).limit(1))).scalar_one()
    response = await client.post("/quest", headers=auth_headers, json={
        "name": "квест",
        "quest_type": "once",
        "stat_id": stat.id,
        "stat_id_2": stat.id,
    })
    assert response.status_code == 422


async def test_other_users_stat_rejected(client, auth_headers, db_session):
    from app.models.user import User
    from app.models.stat import Stat
    from app.core.auth import hash_password

    other = User(username="other", email="other@test.com", password_hash=hash_password("password123"))
    db_session.add(other)
    await db_session.flush()
    other_stat = Stat(user_id=other.id, name="Чужой стат", xp_to_next_level=100)
    db_session.add(other_stat)
    await db_session.commit()

    response = await client.post("/quest", headers=auth_headers, json={
        "name": "квест",
        "quest_type": "once",
        "stat_id_2": other_stat.id,
    })
    assert response.status_code == 404
