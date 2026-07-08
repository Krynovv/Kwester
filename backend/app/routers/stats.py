
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.stat import Stat
from ..schemas.stat import StatRead, StatCreate, StatUpdate


router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("", response_model=list[StatRead])
async def list_stats(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):            
        result = await db.execute(select(Stat).where(Stat.user_id == current_user.id))
        return result.scalars().all()

@router.get("/{stat_id}", response_model=StatRead)
async def get_stat(
    stat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stat = await db.get(Stat, stat_id)
    if stat is None or stat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Stat not found")
    return stat

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

@router.patch("/{stat_id}", response_model=StatRead)
async def update_stat(
    stat_id: int,
    data: StatUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stat = await db.get(Stat, stat_id)
    if stat is None or stat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Stat not found")

    update_data = data.model_dump(exclude_unset=True)

    if stat.is_default and "name" in update_data:
        raise HTTPException(status_code=400, detail="Cannot rename a default stat")

    for field, value in update_data.items():
        setattr(stat, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Stat with this name already exists")

    await db.refresh(stat)
    return stat


@router.delete("/{stat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stat(
    stat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stat = await db.get(Stat, stat_id)
    if stat is None or stat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Stat not found")

    if stat.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete a default stat")
    
    await db.delete(stat)
    await db.commit()
