from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base

if TYPE_CHECKING:
    from .user import User

class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    cost: Mapped[int] = mapped_column(Integer)
    is_purchased: Mapped[bool] = mapped_column(Boolean, default=False)
    unlock_level: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="rewards")

    def __repr__(self) -> str:
        return f"<Reward(id={self.id}, title={self.title}, cost={self.cost})>"
