from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User

class Inventory(Base):
    __tablename__ = "inventories"
    __table_args__ = (UniqueConstraint("user_id", "item_key", name="uq_inventory_user_item"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    item_key: Mapped[str] = mapped_column(String(50))
    charges: Mapped[int] = mapped_column(Integer, default=0)

    users: Mapped["User"] = relationship(back_populates="inventory_items")
