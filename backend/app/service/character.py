from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.stat import Stat

async def get_character_level(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.sum(Stat.level)).where(Stat.user_id == user_id, Stat.is_default == True)
    )
    return result.scalar() or 0
