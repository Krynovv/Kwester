import pytest

from app.models.user import User
from app.models.stat import Stat, CombatRole
from app.core.auth import hash_password
from app.service.character import get_character_level


@pytest.fixture
async def user(db_session):
    u = User(username="leveler", email="leveler@test.com", password_hash=hash_password("password123"))
    db_session.add(u)
    await db_session.flush()
    return u


async def _add_default_stats(db_session, user_id: int, levels: dict[CombatRole, int] | None = None) -> None:
    levels = levels or {}
    for role in CombatRole:
        db_session.add(Stat(
            user_id=user_id,
            name=role.value,
            combat_role=role,
            is_default=True,
            level=levels.get(role, 1),
        ))
    await db_session.flush()


async def test_fresh_account_is_character_level_one(db_session, user):
    """5 базовых статов стартуют с level=1 каждый — персонаж должен быть 1-го
    уровня, а не 5-го (5 * level 1), иначе награды с unlock_level<=5
    открывались бы ещё до первого квеста."""
    await _add_default_stats(db_session, user.id)

    assert await get_character_level(db_session, user.id) == 1


async def test_character_level_tracks_stat_progress(db_session, user):
    await _add_default_stats(db_session, user.id, {CombatRole.strength: 3, CombatRole.agility: 2})

    # +2 (Сила: 3-1) +1 (Ловкость: 2-1) сверх стартового уровня 1
    assert await get_character_level(db_session, user.id) == 4


async def test_character_level_ignores_non_default_stats(db_session, user):
    await _add_default_stats(db_session, user.id)
    db_session.add(Stat(user_id=user.id, name="кастомный стат", level=10, is_default=False))
    await db_session.flush()

    assert await get_character_level(db_session, user.id) == 1


async def test_character_level_with_no_stats_is_one(db_session, user):
    assert await get_character_level(db_session, user.id) == 1
