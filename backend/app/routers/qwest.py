from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..deps import get_current_user
from ..models.user import User
from ..models.quest import Quest
from ..schemas.quest import QuestRead

router = APIRouter(prefix="/quest", tags=["quest"])

@router.get("", responcse_model=list[QuestRead])
async def list_quest(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await fb.execute(select(Quest).where(Quest.user_id == current_user.id))
    return result.scalars().all()


