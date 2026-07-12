from pydantic import BaseModel

class ShopItemRead(BaseModel):
    key: str
    name: str
    description: str
    cost: int
    unlock_level: int
    repeatable: bool
    is_unlocked: bool
    owned_charges: int
