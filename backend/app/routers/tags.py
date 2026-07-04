from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..deps import get_current_user
from ..models.user import User
from ..models.tag import Tag
from ..schemas.tag import TagRead

router = APIRouter(prefix="/tag", tags=["tag"])

@router.get("", response_model=list[TagRead])
async def list_quest(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Tag).where(Tag.user_id == current_user.id))
    return result.scalars().all()

