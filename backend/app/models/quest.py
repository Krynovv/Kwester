from __future__ import annotations
import enum
from datetime import datetime, timezone, date
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Text, Enum, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    tag_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tags.id", ondelete="SET NULL"), nullable=True)
    stat_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("stats.id", ondelete="SET NULL"), nullable=True)
    stat_id_2: Mapped[int | None] = mapped_column(Integer, ForeignKey("stats.id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
                                         
    date_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    date_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    reward_currency: Mapped[int] = mapped_column(Integer, default=0)
    reward_xp: Mapped[int] = mapped_column(Integer, default=0)

    quest_type: Mapped[QuestType] = mapped_column(Enum(QuestType), default=QuestType.once)
    status: Mapped[QuestStatus] = mapped_column(Enum(QuestStatus), default=QuestStatus.active)

    # Только для quest_type == habit. Дни недели, в которые привычка "активна",
    # 0 = понедельник ... 6 = воскресенье (совпадает с date.weekday()).
    # None/пусто -> привычка без расписания (старое поведение: сбрасывается сразу после выполнения).
    scheduled_days: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True, default=None)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    # Служебное поле: последняя дата, до которой уже учтены пропуски расписания
    # (чтобы не штрафовать за один и тот же пропуск повторно при каждом GET /quest).
    streak_checked_until: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)

    # Тоже только для habit. Подмножество scheduled_days со своим временем
    # напоминания: {"0": "08:00", ...} (ключ — день недели строкой, JSON не
    # умеет в int-ключи). День без записи здесь просто не шлёт напоминание.
    reminder_times: Mapped[dict[str, str] | None] = mapped_column(JSONB, nullable=True, default=None)
    # Последняя дата (в поясе пользователя), за которую уже отправлено
    # напоминание — не даёт продублировать отправку при повторном тике цикла.
    last_notified_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)

    tags: Mapped["Tag | None"] = relationship(back_populates="quests")
    users: Mapped["User"] = relationship(back_populates="quests")
    stats: Mapped["Stat | None"] = relationship(
        foreign_keys=[stat_id], back_populates="quests"
    )
    stats_2: Mapped["Stat | None"] = relationship(
        foreign_keys=[stat_id_2], back_populates="quests_secondary"
    )

    def __repr__(self) -> str:
        return f"<Quest(id={self.id}, name={self.name}, status={self.status})>"
