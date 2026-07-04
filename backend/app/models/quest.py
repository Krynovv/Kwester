from __future__ import annotations
import enum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base

if TYPE_CHECKING:
    from .user import User
    from .stat import Stat
    from .tag import Tag


class QuestType(str, enum.Enum):
    once = "once"
    daily = "daily"
    weekly = "weekly"
    habit = "habit"


class QuestStatus(str, enum.Enum):
    active = "active"
    done = "done"
    failed = "failed"


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    tag_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tags.id"), nullable=True)
    stat_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("stats.id"), nullable=True)

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)

    date_start: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reward_currency: Mapped[int] = mapped_column(Integer, default=0)
    reward_xp: Mapped[int] = mapped_column(Integer, default=0)

    quest_type: Mapped[QuestType] = mapped_column(Enum(QuestType), default=QuestType.once)
    status: Mapped[QuestStatus] = mapped_column(Enum(QuestStatus), default=QuestStatus.active)

    tags: Mapped["Tag | None"] = relationship(back_populates="quests")
    users: Mapped["User"] = relationship(back_populates="quests")
    stats: Mapped["Stat | None"] = relationship(back_populates="quests")

    def __repr__(self) -> str:
        return f"<Quest(id={self.id}, name={self.name}, status={self.status})>"
