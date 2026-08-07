from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..core.redis import get_redis
from ..models.user import User
from ..schemas.shop import ShopItemRead
from ..service.shop import list_shop_items, purchase_item

router = APIRouter(prefix="/shop", tags=["shop"])

@router.get("", response_model=list[ShopItemRead])
async def list_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_shop_items(db, current_user.id)

@router.post("/{item_key}/purchase", response_model=ShopItemRead)
async def purchase(
    item_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    return await purchase_item(db, current_user.id, item_key, redis)
