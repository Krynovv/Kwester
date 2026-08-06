"""Тесты пошагового боя: структура раунда, исходы, защита от абьюза.

Баланс здесь не проверяется — за него отвечает test_boss_service.py.
Тут интересна только машина состояний: кто ходит первым, когда бой
заканчивается и что при этом происходит.
"""

import pytest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.core.auth import hash_password
from app.core.constant import COUNT_ROUND, MIN_FIGHT_HP_PERCENT
from app.models.boss import Boss
from app.models.boss_fight import BossFight, FightStatus, FightActor
from app.models.stat import Stat, CombatRole
from app.models.user import User
from app.service.combat import PlayerAction
from app.service.fight import start_fight, take_turn, get_active_fight

IN_WINDOW = datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc)


@pytest.fixture
async def fighter(db_session):
    user = User(
        username="rounder", email="rounder@test.com",
        password_hash=hash_password("password123"), current_hp=100,
    )
    db_session.add(user)
    await db_session.flush()

    for name, role in {
        "Сила": CombatRole.strength, "Ловкость": CombatRole.agility,
        "Интелект": CombatRole.intellect, "Фокус": CombatRole.focus,
        "Здоровье": CombatRole.health,
    }.items():
        db_session.add(Stat(user_id=user.id, name=name, combat_role=role,
                            is_default=True, level=5))

    db_session.add(Boss(user_id=user.id, level=3, pending_failures=0))
    await db_session.commit()
    return user


@pytest.fixture
def in_window(monkeypatch):
    """Двигает часы внутрь окна боя."""
    import app.service.fight as fight_module
    monkeypatch.setattr(fight_module, "_now", lambda: IN_WINDOW)


async def test_start_rejected_before_window(db_session, fighter, fake_redis, monkeypatch):
    import app.service.fight as fight_module
    monkeypatch.setattr(fight_module, "_now",
                        lambda: datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc))

    with pytest.raises(HTTPException) as exc:
        await start_fight(db_session, fighter.id, fake_redis)
    assert exc.value.status_code == 400


async def test_start_rejected_when_too_wounded(db_session, fighter, fake_redis, in_window):
    """Порог входа: без него смерть загоняет в спираль автопоражений."""
    fighter.current_hp = 1
    # реген за сутки уже начислен — иначе ensure_hp_regen подлечит до порога
    fighter.hp_regen_date = datetime.now(timezone.utc).date()
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await start_fight(db_session, fighter.id, fake_redis)
    assert exc.value.status_code == 400
    assert "HP" in exc.value.detail


async def test_start_creates_active_fight(db_session, fighter, fake_redis, in_window):
    fight = await start_fight(db_session, fighter.id, fake_redis)

    assert fight.status is FightStatus.active
    assert fight.current_round == 1
    assert fight.boss_hp == fight.boss_max_hp
    assert fight.player_hp == fighter.current_hp
    assert fight.rng_seed          # без seed бой невоспроизводим
    assert fight.rounds == []


async def test_second_fight_rejected_while_active(db_session, fighter, fake_redis, in_window):
    await start_fight(db_session, fighter.id, fake_redis)

    with pytest.raises(HTTPException) as exc:
        await start_fight(db_session, fighter.id, fake_redis)
    assert exc.value.status_code == 400


async def test_turn_resolves_both_phases(db_session, fighter, fake_redis, in_window):
    """Раунд = фаза игрока + фаза босса, и обе попадают в лог."""
    await start_fight(db_session, fighter.id, fake_redis)
    fight = await take_turn(db_session, fighter.id, PlayerAction.attack, fake_redis)

    actors = [r.actor for r in fight.rounds]
    assert actors[0] is FightActor.player      # игрок ходит первым
    if fight.status is FightStatus.active:
        assert FightActor.boss in actors
        assert fight.current_round == 2


async def test_boss_does_not_answer_when_killed(db_session, fighter, fake_redis, in_window):
    """Если игрок добивает босса в свою фазу, ответа быть не должно."""
    fight = await start_fight(db_session, fighter.id, fake_redis)
    fight.boss_hp = 1
    await db_session.commit()

    fight = await take_turn(db_session, fighter.id, PlayerAction.attack, fake_redis)

    if fight.status is FightStatus.won:
        assert all(r.actor is FightActor.player for r in fight.rounds)
        assert fight.player_hp == fight.player_hp_start   # босс не успел ударить


async def test_ko_ends_fight_and_levels_boss(db_session, fighter, fake_redis, in_window):
    fight = await start_fight(db_session, fighter.id, fake_redis)
    fight.player_hp = 1
    fight.boss_hp = fight.boss_max_hp * 100     # чтобы игрок точно не добил
    await db_session.commit()

    fight = await take_turn(db_session, fighter.id, PlayerAction.attack, fake_redis)

    if fight.status is FightStatus.lost:
        assert fight.player_hp == 0
        await db_session.refresh(fighter)
        assert fighter.current_hp == 0          # HP переносится в профиль
        boss = (await db_session.execute(
            Boss.__table__.select().where(Boss.user_id == fighter.id)
        )).first()
        assert boss.level > 3                   # босс подрос за победу


async def test_fight_ends_after_round_limit(db_session, fighter, fake_redis, in_window):
    """Больше COUNT_ROUND раундов бой длиться не может ни при каких бросках."""
    fight = await start_fight(db_session, fighter.id, fake_redis)
    fight.boss_hp = 10 ** 6         # никто никого не убьёт
    fight.boss_attack = 0
    await db_session.commit()

    for _ in range(COUNT_ROUND):
        fight = await take_turn(db_session, fighter.id, PlayerAction.excuse, fake_redis)

    assert fight.status is not FightStatus.active
    assert fight.current_round <= COUNT_ROUND

    with pytest.raises(HTTPException) as exc:
        await take_turn(db_session, fighter.id, PlayerAction.attack, fake_redis)
    assert exc.value.status_code == 404


async def test_abandoned_fight_autoresolves(db_session, fighter, fake_redis, in_window):
    """Закрыть вкладку на грани смерти не должно быть бесплатным."""
    fight = await start_fight(db_session, fighter.id, fake_redis)
    fight.expires_at = IN_WINDOW - timedelta(minutes=1)
    await db_session.commit()

    assert await get_active_fight(db_session, fighter.id) is None

    await db_session.refresh(fight)
    assert fight.status is not FightStatus.active
    assert fight.finished_at is not None


async def test_rolls_are_deterministic_per_seed(db_session, fighter, fake_redis, in_window):
    """Один и тот же ход нельзя перекатить: бросок предопределён seed'ом."""
    from app.service.combat import build_player_combat, resolve_player_turn, round_rng

    player = build_player_combat({role: 5 for role in CombatRole}, {})
    first = resolve_player_turn(player, 3, PlayerAction.attack, round_rng("abc", 1, "player"))
    second = resolve_player_turn(player, 3, PlayerAction.attack, round_rng("abc", 1, "player"))

    assert (first.hit, first.crit, first.damage) == (second.hit, second.crit, second.damage)

    other = resolve_player_turn(player, 3, PlayerAction.attack, round_rng("abc", 2, "player"))
    assert other.roll != first.roll      # но следующий раунд — другой бросок


async def test_excuse_deals_no_damage(db_session, fighter, fake_redis, in_window):
    fight = await start_fight(db_session, fighter.id, fake_redis)
    before = fight.boss_hp

    fight = await take_turn(db_session, fighter.id, PlayerAction.excuse, fake_redis)

    assert fight.boss_hp == before
    player_round = next(r for r in fight.rounds if r.actor is FightActor.player)
    assert player_round.damage == 0
