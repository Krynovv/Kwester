"""Ограничение частоты запросов поверх уже подключённого Redis.

Фиксированное окно (INCR + EXPIRE): на стыке двух окон теоретически пропускает
до 2×limit, но против перебора паролей этого достаточно, а хранить историю
запросов и тянуть отдельную зависимость не требуется.
"""

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis

RATE_LIMIT_PREFIX = "ratelimit:"

# Неудачных попыток входа с одного IP за 15 минут. Считаются только промахи и
# только до первого успеха: за CGNAT мобильного оператора один IP делят сотни
# людей, и лимит на все запросы подряд блокировал бы невиновных.
LOGIN_FAILURE_LIMIT = 10
LOGIN_FAILURE_WINDOW = 15 * 60

# Регистрации с одного IP за час — против массового создания аккаунтов.
# Здесь считаем все попытки: сама по себе успешная регистрация и есть то,
# что мы ограничиваем.
REGISTER_RATE_LIMIT = 10
REGISTER_RATE_WINDOW = 60 * 60


def client_ip(request: Request) -> str:
    """IP клиента.

    X-Forwarded-For намеренно не читаем: заголовок подделывается клиентом, и
    доверие к нему сняло бы лимит полностью. За обратным прокси корректный
    request.client даёт uvicorn с --proxy-headers --forwarded-allow-ips.
    """
    return request.client.host if request.client else "unknown"


def _key(scope: str, identifier: str) -> str:
    return f"{RATE_LIMIT_PREFIX}{scope}:{identifier}"


async def _raise_too_many(redis: Redis, key: str) -> None:
    retry_after = await redis.ttl(key)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Слишком много попыток, попробуйте позже",
        headers={"Retry-After": str(max(retry_after, 1))},
    )


async def check_rate_limit(redis: Redis, scope: str, identifier: str, limit: int) -> None:
    """Бросает 429, если лимит уже исчерпан. Счётчик не трогает."""
    key = _key(scope, identifier)
    hits = await redis.get(key)
    if hits is not None and int(hits) >= limit:
        await _raise_too_many(redis, key)


async def record_attempt(
    redis: Redis, scope: str, identifier: str, window_seconds: int
) -> None:
    """Отмечает попытку, начиная окно с первой из них."""
    key = _key(scope, identifier)
    hits = await redis.incr(key)
    if hits == 1:
        # Без EXPIRE ключ остался бы в Redis навсегда.
        await redis.expire(key, window_seconds)


async def reset_rate_limit(redis: Redis, scope: str, identifier: str) -> None:
    """Снимает накопленные штрафы — вызывается после успешной аутентификации."""
    await redis.delete(_key(scope, identifier))


async def enforce_rate_limit(
    redis: Redis,
    scope: str,
    identifier: str,
    limit: int,
    window_seconds: int,
) -> None:
    """Считает обращение и бросает 429, если лимит на окно исчерпан."""
    await check_rate_limit(redis, scope, identifier, limit)
    await record_attempt(redis, scope, identifier, window_seconds)
