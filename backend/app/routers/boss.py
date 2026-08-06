from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from ..core.database import get_db
from ..core.redis import get_redis
from ..core.deps import get_current_user
from ..models.user import User
from ..schemas.boss import BossStatus, FightRead, TurnRequest
from ..schemas.user import UserRead
from ..service.boss import get_boss_status, heal
from ..service.fight import start_fight, take_turn, get_active_fight

router = APIRouter(prefix="/boss", tags=["boss"])


@router.get("/status", response_model=BossStatus)
async def boss_status(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    return await get_boss_status(db, current_user.id, redis)


@router.post("/fight", response_model=FightRead, status_code=status.HTTP_201_CREATED)
async def boss_fight_start(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Начинает бой. Ходы делаются через POST /boss/fight/turn."""
    return await start_fight(db, current_user.id, redis)


@router.get("/fight", response_model=FightRead)
async def boss_fight_active(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fight = await get_active_fight(db, current_user.id)
    if fight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Активного боя нет")
    return fight


@router.post("/fight/turn", response_model=FightRead)
async def boss_fight_turn(
    payload: TurnRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Разрешает раунд целиком: фаза игрока, затем ответ босса."""
    return await take_turn(db, current_user.id, payload.action, redis)


@router.post("/heal", response_model=UserRead)
async def boss_heal(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    return await heal(db, current_user.id, redis)
