from __future__ import annotations
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column 
from ..core.database import Base

if TYPE_CHECKING:
    from .user import User


class BossFight(Base):
    __tablename__ ="boss_fights"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))

    fight_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    boss_level: Mapped[int] = mapped_column(Integer, default=1)
    boss_hp: Mapped[int] = mapped_column(Integer, default=100)
    
    result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    users: Mapped["User"] = relationship(back_populates="boss_fights")
