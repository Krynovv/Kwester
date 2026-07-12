from datetime import date, datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.boss import Boss
from ..models.boss_fight import BossFight
from ..models.stat import Stat, CombatRole
from ..models.quest import Quest
from ..models.transaction import TransactionLog, TransactionReason
from ..core.constant import (
    BASE_MAX_HP, HP_PER_HEALTH_LEVEL,
    BOSS_BASE_HP, BOSS_HP_PER_LEVEL, BOSS_TIERS, get_boss_name,
    HP_REGEN_PERCENT, EXHAUSTED_REWARD_MULTIPLIER,
    WIN_BASE_CURRENCY, WIN_CURRENCY_PER_BOSS_LEVEL, WIN_BASE_XP,
    HEAL_COST, HEAL_PERCENT, FIGHT_WINDOW_START_HOUR,
)

def calculate_max_hp(health_level: int) -> int:
    return BASE_MAX_HP + health_level * HP_PER_HEALTH_LEVEL

def calculate_boss_hp(boss_level: int) -> int:
    return BOSS_BASE_HP + boss_level * BOSS_HP_PER_LEVEL

async def get_boss_level(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(select(Boss).where(Boss.user_id == user_id))
    boss = result.scalar_one()
    return boss.level

async def _get_stat_by_role(db: AsyncSession, user_id: int, role: CombatRole) -> Stat | None:
    result = await db.execute(
        select(Stat).where(Stat.user_id == user_id, Stat.combat_role == role)        
    )    
    return result.scalar_one_or_none()

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

async def get_boss_status(db: AsyncSession, user_id: int) -> dict:
    await ensure_hp_regen(db, user_id)

    boss_result = await db.execute(select(Boss).where(Boss.user_id == user_id))
    boss = boss_result.scalar_one()

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    health_stat = await _get_stat_by_role(db, user_id, CombatRole.health)
    max_hp = calculate_max_hp(health_stat.level if health_stat else 0)
    boss_hp = calculate_boss_hp(boss.level)

    today = datetime.now(timezone.utc).date()
    fight_result = await db.execute(
        select(BossFight).where(BossFight.user_id == user_id, BossFight.fight_date == today)
    )
    already_fought = fight_result.scalar_one_or_none() is not None

    now_hour = datetime.now(timezone.utc).hour
    window_open = now_hour >= FIGHT_WINDOW_START_HOUR

    return {
        "boss_name": get_boss_name(boss.level),
        "boss_level": boss.level,
        "boss_hp": boss_hp,
        "pending_failures": boss.pending_failures,
        "current_hp": user.current_hp,
        "max_hp": max_hp,
        "already_fought_today": already_fought,
        "fight_window_open": window_open,
    }


async def fight_boss(db: AsyncSession, user_id: int) -> BossFight:
    await ensure_hp_regen(db, user_id)

    now = datetime.now(timezone.utc)
    today = now.date()

    if now.hour < FIGHT_WINDOW_START_HOUR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fight window opens at {FIGHT_WINDOW_START_HOUR}:00 UTC",
        )

    existing_fight = await db.execute(
        select(BossFight).where(BossFight.user_id == user_id, BossFight.fight_date == today)
    )
    if existing_fight.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already fought today")

    boss_result = await db.execute(select(Boss).where(Boss.user_id == user_id).with_for_update())
    boss = boss_result.scalar_one()

    user_result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = user_result.scalar_one()

    strength_stat = await _get_stat_by_role(db, user_id, CombatRole.strength)
    health_stat = await _get_stat_by_role(db, user_id, CombatRole.health)
    intellect_stat = await _get_stat_by_role(db, user_id, CombatRole.intellect)

    distinct_stats_result = await db.execute(
        select(func.count(func.distinct(Quest.stat_id)))
        .join(Stat, Stat.id == Quest.stat_id)
        .where(
            Quest.user_id == user_id,
            Quest.stat_id.is_not(None),
            Stat.is_default == True,
            func.date(Quest.last_completed_at) == today,
        )
    )
    distinct_stats = distinct_stats_result.scalar() or 0

    strength_level = strength_stat.level if strength_stat else 0
    damage_dealt = strength_level * distinct_stats

    
    boss_hp = calculate_boss_hp(boss.level)
    max_hp = calculate_max_hp(health_stat.level if health_stat else 0)

    won = damage_dealt >= boss_hp

    if won:
        intellect_level = intellect_stat.level if intellect_stat else 0
        currency_reward = WIN_BASE_CURRENCY + boss.level * WIN_CURRENCY_PER_BOSS_LEVEL
        currency_reward += intellect_level * 2

        user.boss_currency_balance += currency_reward

        db.add(TransactionLog(
            user_id=user.id,
            amount=currency_reward,
            reason=TransactionReason.boss_defeated,  
        ))

        stats_result = await db.execute(select(Stat).where(Stat.user_id == user_id, Stat.is_default == True))
        default_stats = stats_result.scalars().all()
        xp_share = WIN_BASE_XP // max(len(default_stats), 1)

        for stat in default_stats:
            stat.current_xp += xp_share
            while stat.current_xp >= stat.xp_to_next_level:
                stat.current_xp -= stat.xp_to_next_level
                stat.level += 1
                stat.xp_to_next_level = int(stat.xp_to_next_level * 1.5)

    else:
        deficit_ratio = max(0.0, (boss_hp - damage_dealt) / boss_hp)
        hp_loss = round(deficit_ratio * max_hp)
        user.current_hp = max(0, user.current_hp - hp_loss)

    fight = BossFight(
        user_id=user_id,
        fight_date=today,
        boss_level_at_time=boss.level,
        boss_hp=boss_hp,
        damage_dealt=damage_dealt,
        result="won" if won else "lost",
    )
    db.add(fight)

    boss.level += boss.pending_failures
    boss.pending_failures = 0

    await db.commit()
    await db.refresh(fight)
    return fight


async def heal(db: AsyncSession, user_id: int) -> User:
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
    return user
