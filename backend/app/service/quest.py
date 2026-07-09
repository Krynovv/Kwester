from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.quest import Quest, QuestStatus, QuestType
from ..models.stat import Stat
from ..models.user import User
from ..models.transaction import TransactionLog, TransactionReason
from ..core.constant import EXHAUSTER_REWARD_MULTIPLIER

async def complete_quest(db: AsyncSession, user_id: int, quest_id: int) -> Quest:
    quest = await db.get(Quest, quest_id)

    if quest is None or quest.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quest not found")

    if quest.status != QuestStatus.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quest is not active")

    
    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one()
    
    multiplier = EXHAUSTER_REWARD_MULTIPLIER if user.current_hp == 0 else 1.0
    user.currency_balance += round(quest.reward_currency * multiplier)
    

    db.add(TransactionLog(
        user_id=user.id, 
        amount=quest.reward_currency,
        reason=TransactionReason.quest_completed,
    ))

    if quest.stat_id:
        stat_result = await db.execute(
            select(Stat).where(Stat.id == quest.stat_id).with_for_update()     
        )
        stat = stat_result.scalar_one_or_none()
        stat.current_xp += round(quest.reward_xp * multiplier)
        if stat is not None:
            stat.current_xp += quest.reward_xp
            while stat.current_xp >= stat.xp_to_next_level:
                stat.current_xp -= stat.xp_to_next_level
                stat.level += 1
                stat.xp_to_next_level = int(stat.xp_to_next_level * 1.5)

    quest.last_completed_at = datetime.now(timezone.utc)

    if quest.quest_type == QuestType.habit:
        quest.status = QuestStatus.active      
    else:
        quest.status = QuestStatus.done      
    
    await db.commit()
    await db.refresh(quest)
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
   
async def mark_overdue_quest_failed(db: AsyncSession, user_id: int) -> None:
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
        await db.commit()
