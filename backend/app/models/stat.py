from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..core.database import Base
from typing import TYPE_CHECKING
from sqlalchemy import UniqueConstraint

if TYPE_CHECKING:
    from .user import User
    from .quest import Quest
    from .tag import Tag

class Stat(Base):
    __tablename__ = "stats"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_stat_name"),)
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    name: Mapped[str] = mapped_column(String(50))
    level: Mapped[int] = mapped_column(Integer, default=1)
    current_xp: Mapped[int] = mapped_column (Integer, default=0)
    xp_to_next_level: Mapped[int] = mapped_column (Integer, default=100)

    users: Mapped["User"] = relationship( back_populates="stats")
    quests: Mapped[list["Quest"]] = relationship(back_populates="stats")
    tags: Mapped[list["Tag"]] = relationship(back_populates="stats")

    def __repr__(self):
        return f"<Stat(id={self.id}, name={self.name})>"
