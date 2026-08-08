"""Границы суток считаются в поясе пользователя, а не в UTC.

Пояс во всех тестах — Europe/Moscow (UTC+3), и моменты подобраны так, что
UTC-дата и местная дата расходятся: под старой логикой каждый из этих
тестов падал бы.
"""

import pytest
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select

from app.core.auth import hash_password
from app.core.timezones import resolve_zone, to_local_date
from app.models.boss import Boss
from app.models.quest import Quest, QuestStatus, QuestType
from app.models.stat import Stat, CombatRole
from app.models.user import User
from app.service.boss import fight_boss, get_boss_status
from app.service.quest import complete_quest, refresh_recurring_quests

MOSCOW = "Europe/Moscow"


@pytest.fixture
async def moscow_user(db_session):
    u = User(
        username="muscovite",
        email="muscovite@test.com",
        password_hash=hash_password("password123"),
        timezone=MOSCOW,
    )
    db_session.add(u)
    await db_session.flush()
    return u


# --- чистые хелперы ---

def test_to_local_date_shifts_across_midnight():
    # 22:00 UTC — это уже следующий день в Москве.
    moment = datetime(2026, 8, 7, 22, 0, tzinfo=timezone.utc)
    assert to_local_date(moment, resolve_zone(MOSCOW)) == date(2026, 8, 8)
    assert to_local_date(moment, resolve_zone("UTC")) == date(2026, 8, 7)


def test_resolve_zone_falls_back_to_utc_on_garbage():
    # Пояс мог исчезнуть после обновления tzdata — падать нельзя.
    assert resolve_zone("Mars/Olympus_Mons").key == "UTC"
    assert resolve_zone(None).key == "UTC"
    assert resolve_zone("").key == "UTC"


# --- привычки и серии ---

async def test_habit_completed_after_utc_midnight_counts_as_local_today(
    db_session, moscow_user, fake_redis, freeze_time
):
    """Главный сценарий: закрыть привычку в час ночи по местному времени.

    01:00 МСК — это 22:00 предыдущих суток по UTC. Раньше выполнение
    засчитывалось во вчера и рвало серию.
    """
    quest = Quest(
        user_id=moscow_user.id,
        name="зал пн/ср/пт",
        quest_type=QuestType.habit,
        scheduled_days=[0, 2, 4],
        date_start=datetime(2026, 8, 3, 5, 0, tzinfo=timezone.utc),
        last_completed_at=datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc),  # пн
        current_streak=1,
        streak_checked_until=date(2026, 8, 3),
    )
    db_session.add(quest)
    await db_session.flush()

    # 22:00 UTC вторника == 01:00 МСК среды, а среда есть в расписании.
    freeze_time(datetime(2026, 8, 4, 22, 0, tzinfo=timezone.utc))

    hp_before = moscow_user.current_hp
    result = await complete_quest(db_session, moscow_user.id, quest.id, fake_redis)

    assert result.current_streak == 2
    assert result.streak_checked_until == date(2026, 8, 5)

    # По местному времени это среда — день расписания, значит штрафа за
    # внеплановое выполнение быть не должно. По UTC был бы вторник и штраф.
    await db_session.refresh(moscow_user)
    assert moscow_user.current_hp == hp_before


async def test_habit_cannot_be_completed_twice_within_one_local_day(
    db_session, moscow_user, fake_redis, freeze_time
):
    quest = Quest(
        user_id=moscow_user.id,
        name="зарядка",
        quest_type=QuestType.habit,
        scheduled_days=[0, 1, 2, 3, 4, 5, 6],
        date_start=datetime(2026, 8, 4, 5, 0, tzinfo=timezone.utc),
        streak_checked_until=date(2026, 8, 4),
    )
    db_session.add(quest)
    await db_session.flush()

    # 4 авг 22:00 UTC и 5 авг 10:00 UTC — разные сутки по UTC, но оба
    # приходятся на 5 августа по Москве.
    freeze_time(datetime(2026, 8, 4, 22, 0, tzinfo=timezone.utc))
    await complete_quest(db_session, moscow_user.id, quest.id, fake_redis)

    freeze_time(datetime(2026, 8, 5, 10, 0, tzinfo=timezone.utc))
    with pytest.raises(HTTPException) as exc_info:
        await complete_quest(db_session, moscow_user.id, quest.id, fake_redis)
    assert exc_info.value.status_code == 400


async def test_daily_quest_resets_on_local_midnight(
    db_session, moscow_user, fake_redis, freeze_time
):
    quest = Quest(
        user_id=moscow_user.id,
        name="ежедневка",
        quest_type=QuestType.daily,
        status=QuestStatus.done,
        # 20:00 UTC == 23:00 МСК того же дня
        last_completed_at=datetime(2026, 8, 4, 20, 0, tzinfo=timezone.utc),
    )
    db_session.add(quest)
    await db_session.flush()

    # 21:30 UTC == 00:30 МСК следующего дня: местные сутки сменились.
    freeze_time(datetime(2026, 8, 4, 21, 30, tzinfo=timezone.utc))
    await refresh_recurring_quests(db_session, moscow_user.id)
    await db_session.refresh(quest)
    assert quest.status == QuestStatus.active


async def test_daily_quest_does_not_reset_before_local_midnight(
    db_session, moscow_user, fake_redis, freeze_time
):
    quest = Quest(
        user_id=moscow_user.id,
        name="ежедневка",
        quest_type=QuestType.daily,
        status=QuestStatus.done,
        # 22:00 UTC 4 августа == 01:00 МСК 5 августа
        last_completed_at=datetime(2026, 8, 4, 22, 0, tzinfo=timezone.utc),
    )
    db_session.add(quest)
    await db_session.flush()

    # 10:00 UTC 5 августа == 13:00 МСК того же местного дня, что и выполнение,
    # хотя по UTC сутки уже сменились.
    freeze_time(datetime(2026, 8, 5, 10, 0, tzinfo=timezone.utc))
    await refresh_recurring_quests(db_session, moscow_user.id)
    await db_session.refresh(quest)
    assert quest.status == QuestStatus.done


# --- бой ---

@pytest.fixture
async def moscow_fighter(db_session, moscow_user):
    for name, role in {
        "Сила": CombatRole.strength,
        "Ловкость": CombatRole.agility,
        "Интелект": CombatRole.intellect,
        "Фокус": CombatRole.focus,
        "Здоровье": CombatRole.health,
    }.items():
        db_session.add(
            Stat(user_id=moscow_user.id, name=name, combat_role=role, is_default=True, level=1)
        )
    db_session.add(Boss(user_id=moscow_user.id, level=1, pending_failures=0))
    await db_session.flush()
    return moscow_user


async def test_projected_damage_counts_quest_finished_after_utc_midnight(
    db_session, moscow_fighter, fake_redis, freeze_time
):
    """Дата выполнения вынимается из SQL уже в поясе игрока.

    Голый func.date() по UTC отбрасывал бы вечерние выполнения в следующий
    день и обнулял их вклад в урон.
    """
    strength = await db_session.execute(
        select(Stat).where(Stat.user_id == moscow_fighter.id, Stat.combat_role == CombatRole.strength)
    )
    strength_stat = strength.scalar_one()

    db_session.add(Quest(
        user_id=moscow_fighter.id,
        stat_id=strength_stat.id,
        name="вечерний квест",
        quest_type=QuestType.once,
        status=QuestStatus.done,
        # 22:00 UTC 7 августа == 01:00 МСК 8 августа
        last_completed_at=datetime(2026, 8, 7, 22, 0, tzinfo=timezone.utc),
    ))
    await db_session.commit()

    # Полдень 8 августа по Москве — тот же местный день, что и выполнение.
    freeze_time(datetime(2026, 8, 8, 9, 0, tzinfo=timezone.utc))

    status_data = await get_boss_status(db_session, moscow_fighter.id, fake_redis)
    assert status_data["projected_damage"] > 0


async def test_fight_window_opens_on_local_hour(
    db_session, moscow_fighter, fake_redis, freeze_time
):
    # 15:00 UTC == 18:00 МСК: окно (с 17:00) уже открыто по местному времени,
    # хотя по UTC ещё закрыто.
    freeze_time(datetime(2026, 8, 8, 15, 0, tzinfo=timezone.utc))

    fight = await fight_boss(db_session, moscow_fighter.id, fake_redis)
    assert fight.result == "lost"  # урона нет, важен сам факт допуска к бою
    assert fight.fight_date == date(2026, 8, 8)


@pytest.fixture
async def new_york_fighter(db_session):
    """Пояс западнее UTC — проверяет смещение в обратную сторону.

    В августе Нью-Йорк на UTC-4, поэтому местный час меньше UTC-часа: только
    так ловится случай «по UTC окно уже открыто, а у игрока ещё день».
    """
    u = User(
        username="newyorker",
        email="newyorker@test.com",
        password_hash=hash_password("password123"),
        timezone="America/New_York",
    )
    db_session.add(u)
    await db_session.flush()

    db_session.add(Stat(
        user_id=u.id, name="Здоровье", combat_role=CombatRole.health, is_default=True, level=1
    ))
    db_session.add(Boss(user_id=u.id, level=1, pending_failures=0))
    await db_session.flush()
    return u


async def test_fight_rejected_before_local_window(
    db_session, new_york_fighter, fake_redis, freeze_time
):
    # 19:00 UTC == 15:00 в Нью-Йорке: по UTC окно (с 17:00) открыто,
    # по местному времени — ещё нет.
    freeze_time(datetime(2026, 8, 8, 19, 0, tzinfo=timezone.utc))

    with pytest.raises(HTTPException) as exc_info:
        await fight_boss(db_session, new_york_fighter.id, fake_redis)
    assert exc_info.value.status_code == 400


# --- API ---

async def test_register_stores_timezone(client):
    response = await client.post("/auth/register", json={
        "username": "tzuser",
        "email": "tzuser@test.com",
        "password": "password123",
        "timezone": MOSCOW,
    })
    assert response.status_code == 201
    assert response.json()["timezone"] == MOSCOW


async def test_register_defaults_to_utc(client):
    response = await client.post("/auth/register", json={
        "username": "notzuser",
        "email": "notzuser@test.com",
        "password": "password123",
    })
    assert response.status_code == 201
    assert response.json()["timezone"] == "UTC"


async def test_register_rejects_invalid_timezone(client):
    response = await client.post("/auth/register", json={
        "username": "badtz",
        "email": "badtz@test.com",
        "password": "password123",
        "timezone": "Mars/Olympus_Mons",
    })
    assert response.status_code == 422


async def test_patch_me_updates_timezone(client):
    await client.post("/auth/register", json={
        "username": "mover",
        "email": "mover@test.com",
        "password": "password123",
    })
    login = await client.post("/auth/token", data={
        "username": "mover",
        "password": "password123",
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.patch("/users/me", json={"timezone": MOSCOW}, headers=headers)
    assert response.status_code == 200
    assert response.json()["timezone"] == MOSCOW

    me = await client.get("/users/me", headers=headers)
    assert me.json()["timezone"] == MOSCOW


async def test_patch_me_rejects_invalid_timezone(client):
    await client.post("/auth/register", json={
        "username": "badmover",
        "email": "badmover@test.com",
        "password": "password123",
    })
    login = await client.post("/auth/token", data={
        "username": "badmover",
        "password": "password123",
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.patch(
        "/users/me", json={"timezone": "Mars/Olympus_Mons"}, headers=headers
    )
    assert response.status_code == 422


async def test_patch_me_rejects_taken_username(client):
    await client.post("/auth/register", json={
        "username": "occupant",
        "email": "occupant@test.com",
        "password": "password123",
    })
    await client.post("/auth/register", json={
        "username": "challenger",
        "email": "challenger@test.com",
        "password": "password123",
    })
    login = await client.post("/auth/token", data={
        "username": "challenger",
        "password": "password123",
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Занятый ник — 400, а не 500 от IntegrityError.
    response = await client.patch("/users/me", json={"username": "occupant"}, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already taken"


async def test_patch_me_allows_keeping_own_username(client):
    await client.post("/auth/register", json={
        "username": "steady",
        "email": "steady@test.com",
        "password": "password123",
    })
    login = await client.post("/auth/token", data={
        "username": "steady",
        "password": "password123",
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Собственное значение не должно считаться конфликтом.
    response = await client.patch(
        "/users/me", json={"username": "steady", "timezone": MOSCOW}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["timezone"] == MOSCOW
