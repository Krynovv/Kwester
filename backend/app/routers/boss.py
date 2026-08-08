
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from ..core.database import get_db
from ..core.redis import get_redis
from ..core.deps import get_current_user
from ..models.user import User
from ..schemas.boss import BossStatus, BossFightResult
from ..schemas.user import UserRead
from ..service.boss import get_boss_status, fight_boss, heal

router = APIRouter(prefix="/boss", tags=["boss"])


@router.get("/status", response_model=BossStatus)
async def boss_status(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    return await get_boss_status(db, current_user.id, redis)


@router.post("/fight", response_model=BossFightResult)
async def boss_fight(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    return await fight_boss(db, current_user.id, redis)


@router.post("/heal", response_model=UserRead)
async def boss_heal(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    return await heal(db, current_user.id, redis)

