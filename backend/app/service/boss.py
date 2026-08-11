import json
from datetime import date
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select, func, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from ..core.timezones import local_now, local_today, resolve_zone
from ..models.user import User
from ..models.boss import Boss
from ..models.boss_fight import BossFight
from ..models.stat import Stat, CombatRole
from ..models.quest import Quest
from ..core.constant import (
    get_boss_name, HP_REGEN_PERCENT, COUNT_ROUND,
    FIGHT_WINDOW_START_HOUR, BOSS_STATUS_CACHE_TTL
)
from ..core.constant_shop import HEAL_COST, HEAL_PERCENT, SPEC_HEALTH_REGEN_BONUS
from .combat import (
    PlayerCombat, build_player_combat, calculate_max_hp, calculate_boss_hp,
    expected_damage_per_round,
)
from .inventory import get_owned_permanent_items

__all__ = ["calculate_max_hp", "calculate_boss_hp", "get_boss_level",
           "get_boss_status", "heal", "ensure_hp_regen",
           "load_combat_profile", "invalidate_boss_status"]

async def get_boss_level(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(select(Boss).where(Boss.user_id == user_id))
    boss = result.scalar_one()
    return boss.level

async def _get_stat_by_role(db: AsyncSession, user_id: int, role: CombatRole) -> Stat | None:
    result = await db.execute(
        select(Stat).where(Stat.user_id == user_id, Stat.combat_role == role)
    )
    return result.scalar_one_or_none()

async def load_combat_profile(db: AsyncSession, user_id: int, today: date, zone: ZoneInfo) -> PlayerCombat:
    """Собирает боевой профиль игрока: уровни статов + закрытые сегодня квесты.

    ВНИМАНИЕ: считает КВЕСТЫ, закрытые сегодня, а не число выполнений. У Quest
    есть только last_completed_at (одно перезаписываемое поле), поэтому две
    отметки привычки за день дают 1. Честный подсчёт требует таблицы
    quest_completions — до неё effort по привычкам занижен.

    Квест может быть привязан к двум статам (stat_id/stat_id_2) — в effort
    обоих затронутых статов он засчитывается отдельно, иначе второй слот
    никак не влиял бы на бой. today — уже локальная дата игрока: голый
    func.date() на UTC-поле отрезал бы вечерние по местному времени
    выполнения в следующий UTC-день.
    """
    stats_result = await db.execute(
        select(Stat).where(Stat.user_id == user_id, Stat.is_default == True)
    )
    levels = {
        stat.combat_role: stat.level
        for stat in stats_result.scalars().all()
        if stat.combat_role is not None
    }

    local_completed_at = func.timezone(zone.key, Quest.last_completed_at)
    completed_today = (
        Quest.user_id == user_id,
        func.date(local_completed_at) == today,
    )
    # union_all, не union: нужен подсчёт квестов на стат, а не факт "затронут"
    # — union() схлопнул бы две разные привязанные к силе привычки в одну
    # строку и точность/уклонение занизились бы вдвое от реального effort.
    touched_stats = union_all(
        select(Quest.id, Quest.stat_id.label("stat_id")).where(*completed_today, Quest.stat_id.is_not(None)),
        select(Quest.id, Quest.stat_id_2.label("stat_id")).where(*completed_today, Quest.stat_id_2.is_not(None)),
    ).subquery()

    quests_result = await db.execute(
        select(Stat.combat_role, func.count(touched_stats.c.stat_id))
        .select_from(touched_stats)
        .join(Stat, Stat.id == touched_stats.c.stat_id)
        .where(Stat.is_default == True, Stat.combat_role.is_not(None))
        .group_by(Stat.combat_role)
    )
    quests_completed = {role: count for role, count in quests_result.all()}
    owned_permanent = frozenset(await get_owned_permanent_items(db, user_id))

    return build_player_combat(levels, quests_completed, owned_permanent)


async def ensure_hp_regen(db: AsyncSession, user_id: int) -> None:
    """Проверка востановление HP за сутки"""
    result = await db.execute(select(User).where(User.id == user_id). with_for_update())
    user = result.scalar_one()

    today = local_today(resolve_zone(user.timezone))
    if user.hp_regen_date == today:
        return

    health_stat = await _get_stat_by_role(db, user_id, CombatRole.health)
    max_hp = calculate_max_hp(health_stat.level if health_stat else 0)

    owned_permanent = await get_owned_permanent_items(db, user_id)
    regen_percent = HP_REGEN_PERCENT + (
        SPEC_HEALTH_REGEN_BONUS if "spec_health" in owned_permanent else 0
    )

    if user.hp_regen_date is None:
        days_passed = 1
    else:
        days_passed = (today - user.hp_regen_date).days

    for _ in range(max(days_passed, 0)):
        if user.current_hp >= max_hp:
            break
        user.current_hp = min(max_hp, user.current_hp + round(max_hp * regen_percent))

    user.hp_regen_date = today
    await db.commit()

def _boss_cache_key(user_id: int) -> str:
    return f"boss:status:{user_id}"

async def invalidate_boss_status(redis: Redis, user_id: int) -> None:
    await redis.delete(_boss_cache_key(user_id))

async def get_boss_status(db: AsyncSession, user_id: int, redis: Redis) -> dict:
    await ensure_hp_regen(db, user_id)

    cache_key = _boss_cache_key(user_id)
    cached = await redis.get(cache_key)
    if cached is not None:
        return json.loads(cached)

    boss_result = await db.execute(select(Boss).where(Boss.user_id == user_id))
    boss = boss_result.scalar_one()

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    zone = resolve_zone(user.timezone)
    today = local_today(zone)
    profile = await load_combat_profile(db, user_id, today, zone)
    max_hp = profile.max_hp
    boss_hp = calculate_boss_hp(profile.avg_level, boss.level)

    fight_result = await db.execute(
        select(BossFight).where(BossFight.user_id == user_id, BossFight.fight_date == today).limit(1)
    )
    already_fought = fight_result.scalar_one_or_none() is not None

    # Окно боя — вечернее по местному времени игрока, а не по UTC.
    window_open = local_now(zone).hour >= FIGHT_WINDOW_START_HOUR

    # Урон за весь бой, если игрок продержится все раунды.
    projected_damage = round(expected_damage_per_round(profile, boss.level) * COUNT_ROUND)

    result = {
        "boss_name": get_boss_name(boss.level),
        "boss_level": boss.level,
        "boss_hp": boss_hp,
        "projected_damage": projected_damage,
        "is_ready": projected_damage >= boss_hp,
        "pending_failures": boss.pending_failures,
        "current_hp": user.current_hp,
        "max_hp": max_hp,
        "already_fought_today": already_fought,
        "fight_window_open": window_open,
    }

    await redis.set(cache_key, json.dumps(result), ex=BOSS_STATUS_CACHE_TTL)
    return result


async def heal(db: AsyncSession, user_id: int, redis: Redis) -> User:
    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one()

    if user.boss_currency_balance < HEAL_COST:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недостаточно особой валюты")

    health_stat = await _get_stat_by_role(db, user_id, CombatRole.health)
    max_hp = calculate_max_hp(health_stat.level if health_stat else 0)

    user.boss_currency_balance -= HEAL_COST
    user.current_hp = min(max_hp, user.current_hp + round(max_hp * HEAL_PERCENT))

    await db.commit()
    await db.refresh(user)
    await invalidate_boss_status(redis, user_id)
    return user
