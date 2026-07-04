from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .quest import Quest
    from .user import User
    from .stat import Stat

class Tag(Base):
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(50))
    linked_stat_id: Mapped[int | None] = mapped_column(ForeignKey("stats.id"))
    
    quests: Mapped[list["Quest"]] = relationship(back_populates="tags")
    users: Mapped["User"] = relationship(back_populates="tags")
    stats: Mapped["Stat | None"] = relationship(back_populates="tags") 

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"
