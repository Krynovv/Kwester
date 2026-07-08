from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base

if TYPE_CHECKING:
    from .user import User


class BossFight(Base):
    __tablename__ ="boss_fights"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    fight_date: Mapped[date] = mapped_column(Date)
    
    boss_hp: Mapped[int] = mapped_column(Integer)
    damage_dealt: Mapped[int] = mapped_column(Integer)
    boss_level_at_time: Mapped[int] = mapped_column(Integer)
    result: Mapped[str | None] = mapped_column(String(20))
    
    users: Mapped["User"] = relationship(back_populates="boss_fights")
