from __future__ import annotations
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column, 
from datetime import datetime
from ..database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .quest import Quest
    from .stat import Stat
    from .tag import Tag

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, datetime=datetime.utcnow)
    image_file: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    
    quests: Mapped[list["Quest"]] = relationship(back_populates="users")
    tags: Mapped[list["Tag"]] = relationship(back_populates="users")
    stats: Mapped[list["Stat"]] = relationship(back_populates="users")

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"
