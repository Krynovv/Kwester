from sqlalchemy import Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..core.database import Base
from typing import TYPE_CHECKING
from sqlalchemy import UniqueConstraint
import enum 

class CombatRole(str, enum.Enum):
    health = "health"
    strength = "strength"
    agility = "agility"
    focus = "focus"
    intellect = "intellect"

if TYPE_CHECKING:
    from .user import User
    from .quest import Quest
    from .tag import Tag

class Stat(Base):
    __tablename__ = "stats"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_stat_name"),)
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(50))
    level: Mapped[int] = mapped_column(Integer, default=1)
    current_xp: Mapped[int] = mapped_column (Integer, default=0)
    # Должен совпадать с core.constant.STAT_LEVEL_XP_BASE.
    xp_to_next_level: Mapped[int] = mapped_column (Integer, default=75)

    combat_role: Mapped[CombatRole | None] = mapped_column(Enum(CombatRole), nullable=True, default=None)
    is_default: Mapped[bool] = mapped_column(default=False)

    users: Mapped["User"] = relationship( back_populates="stats")
    quests: Mapped[list["Quest"]] = relationship(
        foreign_keys="[Quest.stat_id]", back_populates="stats"
    )
    quests_secondary: Mapped[list["Quest"]] = relationship(
        foreign_keys="[Quest.stat_id_2]", back_populates="stats_2"
    )
    tags: Mapped[list["Tag"]] = relationship(back_populates="stats")

    def __repr__(self):
        return f"<Stat(id={self.id}, name={self.name})>"
