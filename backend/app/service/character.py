from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.stat import Stat

async def get_character_level(db: AsyncSession, user_id: int) -> int:
    """Уровень персонажа = 1 + суммарный прогресс сверх стартового level=1 по
    каждому из 5 базовых статов. Без вычитания стартовой единицы свежий
    аккаунт уже читался бы как уровень 5 (5 статов × level 1), ещё до
    первого квеста — и предметы/награды с unlock_level<=5 открывались бы
    сразу после регистрации."""
    result = await db.execute(
        select(func.sum(Stat.level - 1)).where(Stat.user_id == user_id, Stat.is_default == True)
    )
    return 1 + (result.scalar() or 0)
