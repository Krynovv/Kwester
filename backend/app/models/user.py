from __future__ import annotations
from app.models.reward import Reward
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone
from ..core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .quest import Quest
    from .stat import Stat
    from .tag import Tag
    from .transaction import TransactionLog
    from .reward import Reward
    from .boss import Boss
    from .boss_fight import BossFight

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    image_file: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    
    currency_balance: Mapped[int] = mapped_column(Integer, default=0)
    current_hp: Mapped[int] = mapped_column(Integer, default=100)
    boss_currency_balance: Mapped[int] = mapped_column(Integer, default=0)

    quests: Mapped[list["Quest"]] = relationship(back_populates="users")
    tags: Mapped[list["Tag"]] = relationship(back_populates="users")
    stats: Mapped[list["Stat"]] = relationship(back_populates="users")
    transactions: Mapped[list["TransactionLog"]] = relationship(back_populates="user")
    rewards: Mapped[list["Reward"]] = relationship(back_populates="user")
    boss_fights: Mapped[list["BossFight"]] = relationship(back_populates="users")
    boss: Mapped[list["Boss | None"]] = relationship(back_populates="users")

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"
