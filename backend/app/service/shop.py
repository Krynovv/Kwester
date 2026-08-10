from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from ..core.constant_shop import SHOP_ITEMS
from ..models.user import User
from ..models.stat import Stat, CombatRole
from ..models.transaction import TransactionLog, TransactionReason
from ..schemas.shop import ShopItemRead
from .boss import calculate_max_hp, invalidate_boss_status
from .character import get_character_level
from .inventory import consume_charge, get_charges, grant_charge


async def _to_read(db: AsyncSession, user_id: int, key: str, character_level: int) -> ShopItemRead:
    item = SHOP_ITEMS[key]
    owned = await get_charges(db, user_id, key)
    return ShopItemRead(
        key=key,
        name=item["name"],
        description=item["description"],
        cost=item["cost"],
        unlock_level=item["unlock_level"],
        repeatable=item["repeatable"],
        is_unlocked=item["unlock_level"] <= character_level,
        owned_charges=owned,
        permanent=item["permanent"],
        category=item["category"],
    )


async def list_shop_items(db: AsyncSession, user_id: int) -> list[ShopItemRead]:
    character_level = await get_character_level(db, user_id)
    return [await _to_read(db, user_id, key, character_level) for key in SHOP_ITEMS]


async def _apply_heal_100(db: AsyncSession, user: User) -> None:
    result = await db.execute(
        select(Stat).where(Stat.user_id == user.id, Stat.combat_role == CombatRole.health)
    )
    health_stat = result.scalar_one_or_none()
    max_hp = calculate_max_hp(health_stat.level if health_stat else 0)
    user.current_hp = max_hp


# Расходники без боевой категории (сейчас — только heal_100) пьются не
# сразу при покупке, а вручную из инвентаря через use_item: иначе зелье
# исцеления тратится впустую, если HP и так почти полное. Боевые
# расходники (FIGHT_CONSUMABLE_KEYS) сюда не входят — их эффект срабатывает
# в бою (см. service/fight.py), а не через этот эндпоинт.
USE_HANDLERS = {
    "heal_100": _apply_heal_100,
}


async def purchase_item(db: AsyncSession, user_id: int, item_key: str) -> ShopItemRead:
    item = SHOP_ITEMS.get(item_key)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    character_level = await get_character_level(db, user_id)
    if item["unlock_level"] > character_level:
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

    await grant_charge(db, user.id, item_key)

    await db.commit()
    return await _to_read(db, user_id, item_key, character_level)


async def use_item(db: AsyncSession, user_id: int, item_key: str, redis: Redis) -> ShopItemRead:
    item = SHOP_ITEMS.get(item_key)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    handler = USE_HANDLERS.get(item_key)
    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот предмет применяется в бою, а не из инвентаря",
        )

    if not await consume_charge(db, user_id, item_key):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нет заряда")

    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one()
    await handler(db, user)

    await db.commit()
    # handler'ы двигают current_hp (сейчас — только _apply_heal_100), а он
    # часть закэшированного boss:status — без инвалидации GET /boss/status
    # ещё до BOSS_STATUS_CACHE_TTL секунд отдавал бы старое HP.
    await invalidate_boss_status(redis, user_id)
    character_level = await get_character_level(db, user_id)
    return await _to_read(db, user_id, item_key, character_level)
