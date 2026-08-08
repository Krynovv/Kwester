from datetime import date, datetime, timedelta, timezone
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.quest import Quest, QuestStatus, QuestType
from ..models.stat import Stat
from ..models.user import User
from ..models.boss import Boss
from ..models.transaction import TransactionLog, TransactionReason
from .boss import invalidate_boss_status
from .character import apply_stat_xp
from ..core.constant import (
    EXHAUSTED_REWARD_MULTIPLIER,
    OFF_SCHEDULE_HP_PENALTY,
    SECONDARY_STAT_XP_SHARE,
    STREAK_LOOKBACK_DAYS,
)


def _missed_due_dates(quest: Quest, today: date) -> list[date]:
    """Дни расписания, пропущенные с последней проверки, строго до today.

    Окно ограничено STREAK_LOOKBACK_DAYS: streak_checked_until пуст у привычки,
    которой расписание проставили уже после создания, и без ограничения первый же
    GET начислил бы штраф за каждый день её жизни.
    """
    floor = quest.streak_checked_until or (quest.date_start.date() - timedelta(days=1))
    # floor исключается из перебора, поэтому +1 — иначе окно вышло бы на день короче
    floor = max(floor, today - timedelta(days=STREAK_LOOKBACK_DAYS + 1))

    missed: list[date] = []
    day = floor + timedelta(days=1)
    while day < today:
        if day.weekday() in quest.scheduled_days:
            missed.append(day)
        day += timedelta(days=1)
    return missed


async def _penalize_boss(db: AsyncSession, user_id: int, amount: int) -> None:
    if amount <= 0:
        return
    boss_result = await db.execute(select(Boss).where(Boss.user_id == user_id).with_for_update())
    boss = boss_result.scalar_one_or_none()
    if boss:
        boss.pending_failures += amount


async def complete_quest(db: AsyncSession, user_id: int, quest_id: int, redis: Redis) -> Quest:
    quest = await db.get(Quest, quest_id)

    if quest is None or quest.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quest not found")

    if quest.status != QuestStatus.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quest is not active")

    now = datetime.now(timezone.utc)
    today = now.date()
    is_scheduled_habit = quest.quest_type == QuestType.habit and bool(quest.scheduled_days)

    if is_scheduled_habit and quest.last_completed_at is not None and quest.last_completed_at.date() == today:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quest already completed today")

    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one()

    multiplier = EXHAUSTED_REWARD_MULTIPLIER if user.current_hp == 0 else 1.0

    reward_amount = round(quest.reward_currency * multiplier)
    user.currency_balance += reward_amount

    db.add(TransactionLog(
        user_id=user.id,
        amount=reward_amount,
        reason=TransactionReason.quest_completed,
    ))

    # До 2 статов на квест: основной получает полный XP, второй — долю от него.
    # Заполнен только второй слот — он и считается основным, иначе пользователь
    # молча терял бы половину награды.
    attached = [sid for sid in (quest.stat_id, quest.stat_id_2) if sid is not None]
    base_xp = quest.reward_xp * multiplier
    xp_by_stat = {
        sid: round(base_xp * (1.0 if position == 0 else SECONDARY_STAT_XP_SHARE))
        for position, sid in enumerate(dict.fromkeys(attached))
    }

    if xp_by_stat:
        stat_result = await db.execute(
            select(Stat).where(Stat.id.in_(xp_by_stat)).with_for_update().order_by(Stat.id)
        )
        for stat in stat_result.scalars().all():
            apply_stat_xp(stat, xp_by_stat[stat.id])

    # Серия (streak) — только для привычек с расписанием.
    if is_scheduled_habit:
        missed = _missed_due_dates(quest, today)
        if missed:
            quest.current_streak = 0
            await _penalize_boss(db, user_id, len(missed))

        quest.current_streak += 1
        quest.best_streak = max(quest.best_streak, quest.current_streak)
        quest.streak_checked_until = today

        # Внеплановая активность засчитывается в серию, но стоит немного HP —
        # иначе привычку "только по понедельникам" можно накручивать каждый день.
        if today.weekday() not in quest.scheduled_days:
            user.current_hp = max(0, user.current_hp - OFF_SCHEDULE_HP_PENALTY)

    quest.last_completed_at = now

    if quest.quest_type == QuestType.habit:
        quest.status = QuestStatus.active
    else:
        quest.status = QuestStatus.done

    await db.commit()
    await db.refresh(quest)
    # Квест мог задеть stat_id/stat_id_2 и last_completed_at — оба входят в
    # projected_damage закэшированного статуса босса.
    await invalidate_boss_status(redis, user_id)
    return quest


RESET_INTERVALS = {
    QuestType.daily: timedelta(days=1),
    QuestType.weekly: timedelta(days=7),
}

async def refresh_recurring_quests(db: AsyncSession, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    today = now.date()
    current_week = now.isocalendar()[:2]

    result = await db.execute(
        select(Quest).where(
            Quest.user_id == user_id,
            Quest.status == QuestStatus.done,
            Quest.quest_type.in_([QuestType.daily, QuestType.weekly]),
        )    
    )
    quests = result.scalars().all()
    
    changed = False
    for quest in quests:
        if quest.last_completed_at is None:
                continue
        if quest.quest_type == QuestType.daily:
            if quest.last_completed_at.date() < today:
                quest.status = QuestStatus.active
                changed = True

        elif quest.quest_type == QuestType.weekly:
            completed_week = quest.last_completed_at.isocalendar()[:2]
            if completed_week < current_week:
                quest.status = QuestStatus.active
                changed = True
    if changed:
        await db.commit()

async def process_scheduled_habits(db: AsyncSession, user_id: int, redis: Redis) -> None:
    """Привычки с расписанием (scheduled_days): пропущенный день расписания
    считается провалом — бьёт по боссу и сбрасывает текущую серию (streak).
    Проверяется лениво при каждом GET /quest, как и mark_overdue_quest_failed."""
    today = datetime.now(timezone.utc).date()

    result = await db.execute(
        select(Quest).where(
            Quest.user_id == user_id,
            Quest.quest_type == QuestType.habit,
            Quest.status == QuestStatus.active,
            func.cardinality(Quest.scheduled_days) > 0,
        )
    )
    quests = result.scalars().all()

    total_missed = 0
    changed = False
    for quest in quests:
        missed = _missed_due_dates(quest, today)
        if missed:
            quest.current_streak = 0
            # today ещё не наступил как "прошедший" — отмечаем проверенным по вчера включительно
            quest.streak_checked_until = today - timedelta(days=1)
            total_missed += len(missed)
            changed = True

    if total_missed:
        await _penalize_boss(db, user_id, total_missed)

    if changed:
        await db.commit()
        # pending_failures бьёт по закэшированному статусу босса, так же как в complete_quest.
        await invalidate_boss_status(redis, user_id)

async def mark_overdue_quest_failed(db: AsyncSession, user_id: int, redis: Redis) -> None:
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Quest).where(
            Quest.user_id == user_id,
            Quest.status == QuestStatus.active,
            Quest.date_end.is_not(None),
            Quest.date_end < now,
        )
    )
    overdue_quests = result.scalars().all()

    for quest in overdue_quests:
        quest.status = QuestStatus.failed
    if overdue_quests:
        boss_result = await db.execute(select(Boss).where(Boss.user_id == user_id).with_for_update())
        boss = boss_result.scalar_one_or_none()
        if boss:
            boss.pending_failures += len(overdue_quests)

        await db.commit()
        await invalidate_boss_status(redis, user_id)
