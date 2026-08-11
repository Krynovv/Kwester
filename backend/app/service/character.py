from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.stat import Stat
from ..core.constant import STAT_LEVEL_XP_BASE, STAT_LEVEL_XP_INCREMENT

async def get_character_level(db: AsyncSession, user_id: int) -> int:
    """Уровень персонажа = 1 + суммарный прогресс сверх стартового level=1 по
    каждому из 5 базовых статов. Без вычитания стартовой единицы свежий
    аккаунт уже показывал бы уровень 5 (5 статов × level 1), ещё до первого квеста."""
    result = await db.execute(
        select(func.sum(Stat.level - 1)).where(Stat.user_id == user_id, Stat.is_default == True)
    )
    return 1 + (result.scalar() or 0)

def apply_stat_xp(stat: Stat, amount: int) -> None:
    """Начисляет XP стату и разруливает level-up (общая логика для quest.py и boss.py)."""
    stat.current_xp += amount
    while stat.current_xp >= stat.xp_to_next_level:
        stat.current_xp -= stat.xp_to_next_level
        stat.level += 1
        stat.xp_to_next_level = STAT_LEVEL_XP_BASE + (stat.level - 1) * STAT_LEVEL_XP_INCREMENT
