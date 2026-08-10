"""Пошаговый бой с боссом: старт, ход, завершение.

Структура: 7 раундов максимум, игрок всегда ходит первым. Раунд разрешается
целиком одним запросом — фаза игрока, затем фаза босса. Если игрок добивает
босса в свою фазу, босс не отвечает.

Исходы:
    won     — HP босса <= 0
    lost    — HP игрока <= 0 (только в фазе босса)
    timeout — 7 раундов прошли, оба живы; решается по доле оставшегося HP
"""

import secrets
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from ..core.constant import (
    COUNT_ROUND, FIGHT_TTL_MINUTES, MIN_FIGHT_HP_PERCENT,
    FIGHT_WINDOW_START_HOUR, DEATH_BOSS_LEVEL_GAIN, BOSS_LEVEL_GAP_CAP,
    TIMEOUT_POINTS_WIN_REWARD, STAT_XP_GROWTH,
    WIN_BASE_CURRENCY, WIN_CURRENCY_PER_BOSS_LEVEL, WIN_CURRENCY_PER_INTELLECT,
    WIN_BASE_XP,
)
from ..core.constant_shop import (
    SHOP_ITEMS, FIGHT_CONSUMABLE_KEYS,
    RAGE_POTION_DILIGENCE_MULTIPLIER, GUARD_POTION_DAMAGE_REDUCTION,
    SECOND_CHANCE_REVIVE_HP_PERCENT, PATIENCE_EXTRA_ROUNDS,
)
from ..models.boss import Boss
from ..models.boss_fight import (
    BossFight, BossFightRound, FightStatus, FightActor, PlayerActionType,
)
from ..models.stat import Stat, CombatRole
from ..models.transaction import TransactionLog, TransactionReason
from ..models.user import User
from .boss import invalidate_boss_status, ensure_hp_regen, load_combat_profile
from .combat import (
    PlayerCombat, PlayerAction, calculate_boss_hp, calculate_boss_attack,
    resolve_player_turn, resolve_boss_turn, round_rng,
)
from .inventory import consume_charge, get_charges


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_finished(fight: BossFight) -> bool:
    return fight.status is not FightStatus.active


async def get_active_fight(db: AsyncSession, user_id: int) -> BossFight | None:
    """Активный бой, если он есть и не протух.

    Протухший добивается здесь же: иначе можно закрыть вкладку на грани
    смерти и бой просто не засчитается.
    """
    result = await db.execute(
        select(BossFight).where(
            BossFight.user_id == user_id,
            BossFight.status == FightStatus.active,
        )
    )
    fight = result.scalar_one_or_none()
    if fight is None:
        return None

    if _now() >= fight.expires_at:
        await _finish(db, fight, *_resolve_on_points(fight))
        await db.commit()
        return None
    return fight


def _resolve_on_points(fight: BossFight) -> tuple[FightStatus, float]:
    """Таймаут решается по доле оставшегося HP — как решение судей в баттле.

    Без этого правила Ловкость обесценивается: прилежный игрок и так не может
    умереть за 7 раундов, и уклонение ни на что бы не влияло.

    Возвращает исход и множитель награды: победа по очкам стоит дешевле
    честного добивания.
    """
    player_share = fight.player_hp / fight.player_max_hp if fight.player_max_hp else 0
    boss_share = fight.boss_hp / fight.boss_max_hp if fight.boss_max_hp else 0
    if player_share > boss_share:
        return FightStatus.won, TIMEOUT_POINTS_WIN_REWARD
    return FightStatus.timeout, 0.0


async def _prepare_consumables(db: AsyncSession, user_id: int, keys: list[str]) -> None:
    """Валидирует и списывает заряды выбранных на этот бой расходников.

    Правило "сумки": без неё — не больше одного расходника; с ней — до двух,
    и только из разных категорий. Иначе, например, защита + знак шанса
    складываются в фактическую неуязвимость (см. artifacts/shop-design.md).
    """
    if not keys:
        return
    if len(keys) != len(set(keys)):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Один и тот же расходник дважды в бой не берут",
        )
    for key in keys:
        if key not in FIGHT_CONSUMABLE_KEYS:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"{key} нельзя взять в бой как расходник",
            )

    if len(keys) > 1:
        if len(keys) > 2:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Не больше двух расходников за бой",
            )
        if await get_charges(db, user_id, "bag") <= 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Второй расходник требует сумку",
            )
        categories = [SHOP_ITEMS[k]["category"] for k in keys]
        if len(set(categories)) != len(categories):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Расходники должны быть из разных категорий",
            )

    for key in keys:
        if await get_charges(db, user_id, key) <= 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Нет заряда: {key}",
            )
    for key in keys:
        await consume_charge(db, user_id, key)


async def start_fight(
    db: AsyncSession, user_id: int, redis: Redis, consumables: list[str] | None = None,
) -> BossFight:
    consumables = consumables or []
    await ensure_hp_regen(db, user_id)

    now = _now()
    today = now.date()

    if now.hour < FIGHT_WINDOW_START_HOUR:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Окно боя открывается в {FIGHT_WINDOW_START_HOUR}:00 UTC",
        )

    existing = await get_active_fight(db, user_id)
    if existing is not None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Бой уже идёт",
        )

    fought_today = await db.execute(
        select(BossFight).where(
            BossFight.user_id == user_id,
            BossFight.fight_date == today,
        ).limit(1)
    )
    if fought_today.scalar_one_or_none() is not None:
        if not await consume_charge(db, user_id, "extra_boss_fight"):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Сегодня уже дрался",
            )

    await _prepare_consumables(db, user_id, consumables)

    boss_result = await db.execute(
        select(Boss).where(Boss.user_id == user_id).with_for_update()
    )
    boss = boss_result.scalar_one()

    user_result = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = user_result.scalar_one()

    profile = await load_combat_profile(db, user_id, today)

    # Порог входа: без него смерть загоняет в спираль — 20% HP на следующий
    # день означают смерть во втором раунде, и так по кругу.
    if user.current_hp < profile.max_hp * MIN_FIGHT_HP_PERCENT:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Слишком мало HP для боя — подлечись или подожди сутки",
        )

    # Ярость/защита фиксируются на старте, как и весь остальной профиль —
    # закрытый посреди боя квест или купленный предмет не должны влиять
    # на уже идущий бой задним числом.
    if "potion_rage" in consumables:
        profile = replace(profile, attack=profile.attack * (1 + RAGE_POTION_DILIGENCE_MULTIPLIER * profile.diligence))

    boss_attack = calculate_boss_attack(profile.max_hp, profile.diligence)
    if "potion_guard" in consumables:
        boss_attack = round(boss_attack * (1 - GUARD_POTION_DAMAGE_REDUCTION))

    boss_hp = calculate_boss_hp(profile.avg_level, boss.level)
    fight = BossFight(
        user_id=user_id,
        fight_date=today,
        boss_level_at_time=boss.level,
        boss_max_hp=boss_hp,
        boss_hp=boss_hp,
        boss_attack=boss_attack,
        player_hp_start=user.current_hp,
        player_hp=user.current_hp,
        player_max_hp=profile.max_hp,
        stats_snapshot=asdict(profile),
        active_consumables=consumables,
        rng_seed=secrets.token_hex(16),
        status=FightStatus.active,
        current_round=1,
        damage_dealt=0,
        started_at=now,
        expires_at=now + timedelta(minutes=FIGHT_TTL_MINUTES),
    )
    db.add(fight)

    await db.commit()
    await db.refresh(fight)
    await invalidate_boss_status(redis, user_id)
    return fight


async def take_turn(
    db: AsyncSession,
    user_id: int,
    action: PlayerAction,
    redis: Redis,
) -> BossFight:
    """Разрешает раунд целиком: фаза игрока, затем фаза босса."""
    fight = await get_active_fight(db, user_id)
    if fight is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Активного боя нет",
        )

    profile = PlayerCombat(**fight.stats_snapshot)
    round_no = fight.current_round

    # ── фаза игрока ──
    player_turn = resolve_player_turn(
        profile, fight.boss_level_at_time, action,
        round_rng(fight.rng_seed, round_no, "player"),
    )
    fight.boss_hp = max(0, fight.boss_hp - player_turn.damage)
    fight.damage_dealt += player_turn.damage

    db.add(BossFightRound(
        fight_id=fight.id,
        round_no=round_no,
        actor=FightActor.player,
        action=PlayerActionType(action.value),
        roll=player_turn.roll,
        hit=player_turn.hit,
        crit=player_turn.crit,
        damage=player_turn.damage,
        target_hp_after=fight.boss_hp,
    ))

    if fight.boss_hp <= 0:
        await _finish(db, fight, FightStatus.won)
        await db.commit()
        await db.refresh(fight)
        await invalidate_boss_status(redis, user_id)
        return fight

    # ── фаза босса ──
    if not player_turn.stuns_boss:
        boss_turn = resolve_boss_turn(
            profile, fight.boss_level_at_time, fight.boss_attack,
            round_rng(fight.rng_seed, round_no, "boss"),
            evasion_bonus=player_turn.evasion_bonus,
        )
        fight.player_hp = max(0, fight.player_hp - boss_turn.damage)

        db.add(BossFightRound(
            fight_id=fight.id,
            round_no=round_no,
            actor=FightActor.boss,
            action=None,
            roll=boss_turn.roll,
            hit=boss_turn.hit,
            crit=boss_turn.crit,
            damage=boss_turn.damage,
            target_hp_after=fight.player_hp,
        ))

        if fight.player_hp <= 0:
            if "token_second_chance" in fight.active_consumables:
                fight.player_hp = round(fight.player_max_hp * SECOND_CHANCE_REVIVE_HP_PERCENT)
                # Переприсваиваем список целиком — JSON-колонка не видит
                # мутации in-place (.remove/.pop) как изменение.
                fight.active_consumables = [
                    key for key in fight.active_consumables if key != "token_second_chance"
                ]
            else:
                await _finish(db, fight, FightStatus.lost)
                await db.commit()
                await db.refresh(fight)
                await invalidate_boss_status(redis, user_id)
                return fight

    round_limit = COUNT_ROUND + (
        PATIENCE_EXTRA_ROUNDS if "token_patience" in fight.active_consumables else 0
    )
    if round_no >= round_limit:
        await _finish(db, fight, *_resolve_on_points(fight))
    else:
        fight.current_round = round_no + 1

    await db.commit()
    await db.refresh(fight)
    await invalidate_boss_status(redis, user_id)
    return fight


async def _finish(
    db: AsyncSession,
    fight: BossFight,
    result: FightStatus,
    award_multiplier: float = 1.0,
) -> None:
    fight.status = result
    fight.finished_at = _now()

    user_result = await db.execute(
        select(User).where(User.id == fight.user_id).with_for_update()
    )
    user = user_result.scalar_one()
    user.current_hp = fight.player_hp

    boss_result = await db.execute(
        select(Boss).where(Boss.user_id == fight.user_id).with_for_update()
    )
    boss = boss_result.scalar_one()

    if result is FightStatus.won:
        await _award(db, user, boss, multiplier=award_multiplier)
    elif result is FightStatus.timeout:
        # Босс выстоял — награды нет, но и уровень не растёт: это не поражение.
        pass
    elif "charm_mercy" not in fight.active_consumables:
        boss.pending_failures += DEATH_BOSS_LEVEL_GAIN

    # Разрыв с игроком не должен расти бесконечно: иначе отставший игрок
    # никогда не догоняет (см. BOSS_LEVEL_GAP_CAP).
    player_avg_level = fight.stats_snapshot["avg_level"]
    boss.level = min(
        boss.level + boss.pending_failures,
        round(player_avg_level) + BOSS_LEVEL_GAP_CAP,
    )
    boss.pending_failures = 0


async def _award(db: AsyncSession, user: User, boss: Boss, multiplier: float) -> None:
    stats_result = await db.execute(
        select(Stat).where(Stat.user_id == user.id, Stat.is_default == True)
    )
    default_stats = stats_result.scalars().all()

    intellect = next(
        (s.level for s in default_stats if s.combat_role is CombatRole.intellect), 0
    )
    currency = (
        WIN_BASE_CURRENCY
        + boss.level * WIN_CURRENCY_PER_BOSS_LEVEL
        + intellect * WIN_CURRENCY_PER_INTELLECT
    )
    currency = round(currency * multiplier)

    user.boss_currency_balance += currency
    db.add(TransactionLog(
        user_id=user.id,
        amount=currency,
        reason=TransactionReason.boss_defeated,
    ))

    xp_share = round(WIN_BASE_XP * multiplier) // max(len(default_stats), 1)
    for stat in default_stats:
        stat.current_xp += xp_share
        while stat.current_xp >= stat.xp_to_next_level:
            stat.current_xp -= stat.xp_to_next_level
            stat.level += 1
            stat.xp_to_next_level = int(stat.xp_to_next_level * STAT_XP_GROWTH)
