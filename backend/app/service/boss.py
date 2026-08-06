import json
from datetime import date, datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from ..models.user import User
from ..models.boss import Boss
from ..models.boss_fight import BossFight
from ..models.stat import Stat, CombatRole
from ..models.quest import Quest
from ..core.constant import (
    get_boss_name, HP_REGEN_PERCENT, COUNT_ROUND,
    FIGHT_WINDOW_START_HOUR, BOSS_STATUS_CACHE_TTL
)
from ..core.constant_shop import HEAL_COST, HEAL_PERCENT
from .combat import (
    PlayerCombat, build_player_combat, calculate_max_hp, calculate_boss_hp,
    expected_damage_per_round,
)

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

async def load_combat_profile(db: AsyncSession, user_id: int, today: date) -> PlayerCombat:
    """Собирает боевой профиль игрока: уровни статов + закрытые сегодня квесты.

    ВНИМАНИЕ: считает КВЕСТЫ, закрытые сегодня, а не число выполнений. У Quest
    есть только last_completed_at (одно перезаписываемое поле), поэтому две
    отметки привычки за день дают 1. Честный подсчёт требует таблицы
    quest_completions — до неё effort по привычкам занижен.
    """
    stats_result = await db.execute(
        select(Stat).where(Stat.user_id == user_id, Stat.is_default == True)
    )
    levels = {
        stat.combat_role: stat.level
        for stat in stats_result.scalars().all()
        if stat.combat_role is not None
    }

    quests_result = await db.execute(
        select(Stat.combat_role, func.count(Quest.id))
        .join(Quest, Quest.stat_id == Stat.id)
        .where(
            Quest.user_id == user_id,
            Stat.is_default == True,
            Stat.combat_role.is_not(None),
            func.date(Quest.last_completed_at) == today,
        )
        .group_by(Stat.combat_role)
    )
    quests_completed = {role: count for role, count in quests_result.all()}

    return build_player_combat(levels, quests_completed)


async def ensure_hp_regen(db: AsyncSession, user_id: int) -> None:
    """Проверка востановление HP за сутки"""
    result = await db.execute(select(User).where(User.id == user_id). with_for_update())
    user = result.scalar_one()

    today = datetime.now(timezone.utc).date()
    if user.hp_regen_date == today:
        return

    health_stat = await _get_stat_by_role(db, user_id, CombatRole.health)
    max_hp = calculate_max_hp(health_stat.level if health_stat else 0)

    if user.hp_regen_date is None:
        days_passed = 1
    else:
        days_passed = (today - user.hp_regen_date).days 
    
    for _ in range(max(days_passed, 0)):
        if user.current_hp >= max_hp:
            break
        user.current_hp = min(max_hp, user.current_hp + round(max_hp * HP_REGEN_PERCENT))
    
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

    today = datetime.now(timezone.utc).date()
    profile = await load_combat_profile(db, user_id, today)
    max_hp = profile.max_hp
    boss_hp = calculate_boss_hp(profile.avg_level, boss.level)

    fight_result = await db.execute(
        select(BossFight).where(BossFight.user_id == user_id, BossFight.fight_date == today).limit(1)
    )
    already_fought = fight_result.scalar_one_or_none() is not None

    now_hour = datetime.now(timezone.utc).hour
    window_open = now_hour >= FIGHT_WINDOW_START_HOUR

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
