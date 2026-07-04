
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..deps import get_current_user
from ..models.user import User
from ..models.stat import Stat
from ..schemas.stat import StatRead

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("", response_model=list[StatRead])
async def list_stats(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):            
        result = await db.execute(select(Stat).where(Stat.user_id == current_user.id))
        return result.scalars().all()

