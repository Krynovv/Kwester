from __future__ import annotations
import enum
from datetime import date, datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    Integer, String, Date, DateTime, ForeignKey, Enum, Boolean, Float, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base

if TYPE_CHECKING:
    from .user import User


class FightStatus(str, enum.Enum):
    active = "active"
    won = "won"
    lost = "lost"       # KO: HP игрока ушло в 0
    timeout = "timeout"  # 7 раундов прошли, оба живы — решается по очкам


class FightActor(str, enum.Enum):
    player = "player"
    boss = "boss"


class PlayerActionType(str, enum.Enum):
    attack = "attack"
    joke = "joke"
    excuse = "excuse"


class BossFight(Base):
    """Состояние боя, а не запись результата.

    Бой живёт между запросами: игрок делает ход, сервер разрешает раунд
    целиком (фаза игрока -> фаза босса) и возвращает обе реплики.
    """

    __tablename__ = "boss_fights"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    fight_date: Mapped[date] = mapped_column(Date)
    boss_level_at_time: Mapped[int] = mapped_column(Integer)

    boss_max_hp: Mapped[int] = mapped_column(Integer)
    boss_hp: Mapped[int] = mapped_column(Integer)
    boss_attack: Mapped[int] = mapped_column(Integer)

    player_hp_start: Mapped[int] = mapped_column(Integer)
    player_hp: Mapped[int] = mapped_column(Integer)
    player_max_hp: Mapped[int] = mapped_column(Integer)

    # Боевой профиль фиксируется на старте: закрытый посреди боя квест
    # не должен усиливать игрока задним числом.
    stats_snapshot: Mapped[dict] = mapped_column(JSON)

    # Броски выводятся из seed — бой воспроизводим, ход нельзя перекатить.
    rng_seed: Mapped[str] = mapped_column(String(64))

    # Расходники, выбранные на старте боя (SHOP_ITEMS ключи, permanent=False).
    # Список меняется в ходе боя (напр. token_second_chance вычищается после
    # срабатывания) — менять только через переприсваивание всего списка,
    # JSON-колонка не отслеживает мутации in-place.
    active_consumables: Mapped[list[str]] = mapped_column(JSON, default=list)

    status: Mapped[FightStatus] = mapped_column(Enum(FightStatus), default=FightStatus.active)
    current_round: Mapped[int] = mapped_column(Integer, default=1)
    damage_dealt: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    users: Mapped["User"] = relationship(back_populates="boss_fights")
    # selectin, а не ленивая загрузка: раунды всегда уходят в ответ вместе с
    # боем, а ленивый доступ в async-контексте роняет MissingGreenlet.
    rounds: Mapped[list["BossFightRound"]] = relationship(
        back_populates="fight",
        cascade="all, delete-orphan",
        order_by="BossFightRound.id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<BossFight(id={self.id}, status={self.status}, round={self.current_round})>"


class BossFightRound(Base):
    """Одна фаза одного раунда. Это одновременно лог для античита и сама
    переписка: по нему фронт перерисовывает чат целиком."""

    __tablename__ = "boss_fight_rounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    fight_id: Mapped[int] = mapped_column(
        ForeignKey("boss_fights.id", ondelete="CASCADE"), index=True
    )

    round_no: Mapped[int] = mapped_column(Integer)
    actor: Mapped[FightActor] = mapped_column(Enum(FightActor))
    action: Mapped[PlayerActionType | None] = mapped_column(
        Enum(PlayerActionType), nullable=True
    )

    roll: Mapped[float] = mapped_column(Float)
    hit: Mapped[bool] = mapped_column(Boolean)
    crit: Mapped[bool] = mapped_column(Boolean, default=False)
    damage: Mapped[int] = mapped_column(Integer, default=0)
    target_hp_after: Mapped[int] = mapped_column(Integer)

    fight: Mapped["BossFight"] = relationship(back_populates="rounds")

    def __repr__(self) -> str:
        return f"<BossFightRound(fight={self.fight_id}, r={self.round_no}, {self.actor})>"
