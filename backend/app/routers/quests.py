from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.deps import get_current_user
from ..core.redis import get_redis
from ..core.timezones import local_today, resolve_zone
from ..models.user import User
from ..models.tag import Tag
from ..models.quest import Quest, QuestType
from ..models.stat import Stat
from ..schemas.quest import QuestRead, QuestCreate, QuestUpdate
from ..service.quest import (
    complete_quest,
    refresh_recurring_quests,
    mark_overdue_quest_failed,
    process_scheduled_habits,
)
from ..core.constant import QUEST_TYPE_REWARDS

router = APIRouter(prefix="/quest", tags=["quest"])


async def _validate_stat(db: AsyncSession, stat_id: int | None, user_id: int) -> None:
    if stat_id is None:
        return
    stat = await db.get(Stat, stat_id)
    if stat is None or stat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Stat not found")


@router.get("", response_model=list[QuestRead])
async def list_quest(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    await refresh_recurring_quests(db, current_user.id)
    await process_scheduled_habits(db, current_user.id, redis)
    await mark_overdue_quest_failed(db, current_user.id, redis)

    result = await db.execute(select(Quest).where(Quest.user_id == current_user.id))
    return result.scalars().all()

@router.get("/{quest_id}", response_model=QuestRead)
async def get_quest(
    quest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quest = await db.get(Quest, quest_id)
    if quest is None or quest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Quest not found")
    return quest

@router.post("", response_model=QuestRead, status_code=status.HTTP_201_CREATED)
async def create_quest(
    data: QuestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.tag_id is not None:
        tag = await db.get(Tag, data.tag_id)
        if tag is None or tag.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Tag not found")

    await _validate_stat(db, data.stat_id, current_user.id)
    await _validate_stat(db, data.stat_id_2, current_user.id)

    rewards = QUEST_TYPE_REWARDS[data.quest_type]

    quest = Quest(
        user_id=current_user.id,
        reward_currency=rewards["currency"],
        reward_xp=rewards["xp"],
        **data.model_dump(),
    )
    if quest.scheduled_days:
        quest.streak_checked_until = local_today(resolve_zone(current_user.timezone))

    db.add(quest)
    await db.commit()
    await db.refresh(quest)
    return quest

@router.post("/{quest_id}/complete", response_model=QuestRead)
async def complete_quest_endpoint(
    quest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    return await complete_quest(db, current_user.id, quest_id, redis)

@router.patch("/{quest_id}", response_model=QuestRead)
async def update_quest(
    quest_id: int,
    data: QuestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quest = await db.get(Quest, quest_id)
    if quest is None or quest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    update_data = data.model_dump(exclude_unset=True)

    if "tag_id" in update_data and update_data["tag_id"] is not None:
        tag = await db.get(Tag, update_data["tag_id"])
        if tag is None or tag.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Stat not found")

    if "stat_id" in update_data:
        await _validate_stat(db, update_data["stat_id"], current_user.id)

    if "stat_id_2" in update_data:
        await _validate_stat(db, update_data["stat_id_2"], current_user.id)

    new_stat_id = update_data.get("stat_id", quest.stat_id)
    new_stat_id_2 = update_data.get("stat_id_2", quest.stat_id_2)
    if new_stat_id is not None and new_stat_id == new_stat_id_2:
        raise HTTPException(status_code=400, detail="stat_id and stat_id_2 must be different stats")

    if "scheduled_days" in update_data and update_data["scheduled_days"] is not None:
        if quest.quest_type != QuestType.habit:
            raise HTTPException(status_code=400, detail="scheduled_days is only allowed for habit quests")

    schedule_changed = (
        "scheduled_days" in update_data
        and update_data["scheduled_days"] != quest.scheduled_days
    )

    for field, value in update_data.items():
        setattr(quest, field, value)

    # Новое расписание — новая серия. Без сброса streak_checked_until пропуски
    # считались бы от даты создания квеста, вплоть до сотен штрафов за один GET.
    if schedule_changed:
        quest.current_streak = 0
        quest.streak_checked_until = (
            local_today(resolve_zone(current_user.timezone)) if quest.scheduled_days else None
        )

    await db.commit()
    await db.refresh(quest)
    return quest

@router.delete("/{quest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quest(
    quest_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quest = await db.get(Quest, quest_id)
    if quest is None or quest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Quest not found")

    await db.delete(quest)
    await db.commit()
