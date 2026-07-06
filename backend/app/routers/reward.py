from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.reward import Reward
from ..schemas.reward import RewardCreate, RewardRead
from ..service.economy import purchase_reward

router = APIRouter(prefix="/rewards", tags=["rewards"])

@router.get("", response_model=list[RewardRead])
asyncd def list_rewards (
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Reward).where(Reward.user_id == current_user.id))
    return result.scalars().all()

@router.post("", response_model=RewardRead, status_code=statis.HTTP_201_CREATED)
async def created_reward(
    data: RewardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reward = Reward(User_id=current_user.id, **data.model_dump())
    db.add(reward)
    await db.commit()
    await db.refresh(reward)
    return reward

@router.post("/{reward.id}/purchase", response_model=RewardRead)
async def purchase_reward_endpoint(
    reward_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await purchase_reward(db, current_user.id, reward.reward_id)
