from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.reward import Reward
from ..schemas.reward import RewardCreate, RewardRead, RewardUpdate
from ..service.economy import purchase_reward

router = APIRouter(prefix="/rewards", tags=["rewards"])

@router.get("", response_model=list[RewardRead])
async def list_rewards (
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    character_level = await get_character_level(db, current_user.id)
    if reward.unlock_level > character_level:
        raise HTTPException(status_code=400, detail="Reward not unlocked yet")
    
    result = await db.execute(select(Reward).where(Reward.user_id == current_user.id))
    return result.scalars().all()

@router.get("/{reward_id}", response_model=RewardRead)
async def get_reward(
    reward_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reward = await db.get(Reward, reward_id)
    if reward is None or reward.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reward not found")
    return reward

@router.post("", response_model=RewardRead, status_code=status.HTTP_201_CREATED)
async def created_reward(
    data: RewardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reward = Reward(user_id=current_user.id, **data.model_dump())
    db.add(reward)
    await db.commit()
    await db.refresh(reward)
    return reward

@router.post("/{reward_id}/purchase", response_model=RewardRead)
async def purchase_reward_endpoint(
    reward_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    character_level = await get_character_level(db, current_user.id)
    if reward.unlock_level > character_level:
        raise HTTPException(status_code=400, detail="Reward not unlocked yet")
    
    return await purchase_reward(db, current_user.id, reward_id)

@router.patch("/{reward_id}", response_model=RewardRead)
async def update_reward(
    reward_id: int,
    data: RewardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reward = await db.get(Reward, reward_id)
    if reward is None or reward.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reward not found")

    if reward.is_purchased:
        raise HTTPException(status_code=400, detail="Cannot edit an already purchased reward")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reward, field, value)

    await db.commit()
    await db.refresh(reward)
    return reward


@router.delete("/{reward_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reward(
    reward_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reward = await db.get(Reward, reward_id)
    if reward is None or reward.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reward not found")

    await db.delete(reward)
    await db.commit()
