from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.constant_shop import SHOP_ITEMS
from ..models.user import User
from ..models.stat import Stat, CombatRole
from ..models.transaction import TransactionLog, TransactionReason
from ..schemas.shop import ShopItemRead
from .boss import get_boss_level, calculate_max_hp
from .inventory import get_charges, grant_charge


async def _to_read(db: AsyncSession, user_id: int, key: str, boss_level: int) -> ShopItemRead:
    item = SHOP_ITEMS[key]
    owned = await get_charges(db, user_id, key)
    return ShopItemRead(
        key=key,
        name=item["name"],
        description=item["description"],
        cost=item["cost"],
        unlock_level=item["unlock_level"],
        repeatable=item["repeatable"],
        is_unlocked=item["unlock_level"] <= boss_level,
        owned_charges=owned,
    )


async def list_shop_items(db: AsyncSession, user_id: int) -> list[ShopItemRead]:
    boss_level = await get_boss_level(db, user_id)
    return [await _to_read(db, user_id, key, boss_level) for key in SHOP_ITEMS]


async def _apply_heal_100(db: AsyncSession, user: User) -> None:
    result = await db.execute(
        select(Stat).where(Stat.user_id == user.id, Stat.combat_role == CombatRole.health)
    )
    health_stat = result.scalar_one_or_none()
    max_hp = calculate_max_hp(health_stat.level if health_stat else 0)
    user.current_hp = max_hp


EFFECT_HANDLERS = {
    "heal_100": _apply_heal_100,
    "extra_boss_fight": lambda db, user: grant_charge(db, user.id, "extra_boss_fight"),
}


async def purchase_item(db: AsyncSession, user_id: int, item_key: str) -> ShopItemRead:
    item = SHOP_ITEMS.get(item_key)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    boss_level = await get_boss_level(db, user_id)
    if item["unlock_level"] > boss_level:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item not unlocked yet")

    if not item["repeatable"] and await get_charges(db, user_id, item_key) > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item already owned")

    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one()

    if user.boss_currency_balance < item["cost"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недостаточно особой валюты")

    user.boss_currency_balance -= item["cost"]

    db.add(TransactionLog(
        user_id=user.id,
        amount=-item["cost"],
        reason=TransactionReason.shop_purchased,
    ))

    await EFFECT_HANDLERS[item_key](db, user)

    await db.commit()
    return await _to_read(db, user_id, item_key, boss_level)
