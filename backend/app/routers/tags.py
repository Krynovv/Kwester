from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.tag import Tag
from ..models.stat import Stat
from ..schemas.tag import TagRead, TagCreate

router = APIRouter(prefix="/tag", tags=["tag"])

@router.get("", response_model=list[TagRead])
async def list_quest(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Tag).where(Tag.user_id == current_user.id))
    return result.scalars().all()

@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def created_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.linked_stat_id is not None:
        stat = await db.get(Stat, data.linked_stat_id)
        if stat is None or stat.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Stat not found")

    tag = Tag(user_id=current_user.id, **data.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag

