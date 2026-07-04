
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.stat import Stat
from ..schemas.stat import StatRead, StatCreate 


router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("", response_model=list[StatRead])
async def list_stats(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):            
        result = await db.execute(select(Stat).where(Stat.user_id == current_user.id))
        return result.scalars().all()

@router.post("", response_model=StatRead, status_code=status.HTTP_201_CREATED)
async def create_stat(
    data: StatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stat = Stat(user_id=current_user.id, **data.model_dump())
    db.add(stat)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Stat with this name already exists")

    await db.refresh(stat)
    return stat
