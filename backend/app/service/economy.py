from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.reward import Reward
from ..models.user import User
from ..models.transaction import TransactionLog, TransactionReason
from ..service.character import get_character_level

async def purchase_reward(db: AsyncSession, user_id:int, reward_id:int) -> Reward:
    reward = await db.get(Reward, reward_id)

    if reward is None or reward.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reward not found")

    if reward.is_purchased and not reward.repeatable:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reward already purchased")

    character_level = await get_character_level(db, user_id)
    if reward.unlock_level > character_level:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reward not unlocked yet")

    result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
    )
    user = result.scalar_one()

    if user.currency_balance < reward.cost:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недостаточно средств")

    user.currency_balance -= reward.cost
    reward.is_purchased = True
    reward.purchase_count += 1

    db.add(TransactionLog(
        user_id=user.id,
        amount=-reward.cost,
        reason=TransactionReason.reward_purchased,
    ))

    await db.commit()
    await db.refresh(reward)
    return reward
