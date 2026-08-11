from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.constant_shop import PERMANENT_ITEM_KEYS
from ..models.inventory import Inventory


async def get_charges(db: AsyncSession, user_id: int, item_key: str) -> int:
    result = await db.execute(
        select(Inventory).where(Inventory.user_id == user_id, Inventory.item_key == item_key)
    )
    row = result.scalar_one_or_none()
    return row.charges if row else 0


async def grant_charge(db: AsyncSession, user_id: int, item_key: str) -> None:
    result = await db.execute(
        select(Inventory).where(Inventory.user_id == user_id, Inventory.item_key == item_key)
    )
    row = result.scalar_one_or_none()
    if row is None:
        db.add(Inventory(user_id=user_id, item_key=item_key, charges=1))
    else:
        row.charges += 1


async def consume_charge(db: AsyncSession, user_id: int, item_key: str) -> bool:
    result = await db.execute(
        select(Inventory)
        .where(Inventory.user_id == user_id, Inventory.item_key == item_key)
        .with_for_update()
    )
    row = result.scalar_one_or_none()
    if row is None or row.charges <= 0:
        return False
    row.charges -= 1
    return True


async def get_owned_permanent_items(db: AsyncSession, user_id: int) -> set[str]:
    """Постоянные предметы (eye_focus, spec_*, bag) не расходуются в бою —
    их наличие просто проверяется. Используется боевым профилем и регеном."""
    result = await db.execute(
        select(Inventory.item_key).where(
            Inventory.user_id == user_id,
            Inventory.item_key.in_(PERMANENT_ITEM_KEYS),
            Inventory.charges > 0,
        )
    )
    return set(result.scalars().all())
