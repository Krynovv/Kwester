from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.tag import Tag
from ..models.quest import Quest
from ..models.stat import Stat
from ..schemas.quest import QuestRead, QuestCreate
from ..service.quest import complete_quest, refresh_recurring_quests, mark_overdue_quest_failed


router = APIRouter(prefix="/quest", tags=["quest"])

@router.get("", response_model=list[QuestRead])
async def list_quest(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await refresh_recurring_quests(db, current_user.id)
    await mark_overdue_quest_failed(db, current_user.id)

    result = await db.execute(select(Quest).where(Quest.user_id == current_user.id))
    return result.scalars().all()


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

    if data.stat_id is not None:
        stat = await db.get(Stat, data.stat_id)
        if stat is None or stat.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Stat not found")

    quest = Quest(
        user_id=current_user.id,
        **data.model_dump(),
    )

    db.add(quest)
    await db.commit()
    await db.refresh(quest)
    return quest

@router.post("/{quest_id}/complete", response_model=QuestRead)
async def complete_quest_endpoint(
    quest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await complete_quest(db, current_user.id, quest_id)


