from __future__ import annotations
import enum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base

if TYPE_CHECKING:
    from .user import User


class TransactionReason(str, enum.Enum):
    quest_completed = "quest_completed"
    reward_purchased = "reward_purchased"
    manual_adjust = "manual_adjust"

class TransactionLog(Base):
    __tablename__ = "transaction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[TransactionReason] = mapped_column(Enum(TransactionReason))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<TransactionLog(id={self.id}, user_id={self.user_id}, amount={self.amount}, reason={self.reason})>"
