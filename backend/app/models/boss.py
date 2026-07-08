from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base

if TYPE_CHECKING:
    from .user import User

class Boss(Base):
    __tablename__ ="bosses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    pending_failures: Mapped[int] = mapped_column(Integer, default=0)

    users: Mapped["User"] = relationship(back_populates="bosses")
