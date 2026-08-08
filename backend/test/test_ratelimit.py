import pytest

from app.core.constant import MAX_REQUEST_BODY_SIZE
from app.core.ratelimit import LOGIN_FAILURE_LIMIT, enforce_rate_limit


async def _register(client, username):
    return await client.post("/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "password123",
    })


async def test_login_rate_limited_after_too_many_failures(client):
    await _register(client, "bruteforced")

    wrong = {"username": "bruteforced", "password": "wrong-password"}
    for _ in range(LOGIN_FAILURE_LIMIT):
        assert (await client.post("/auth/token", data=wrong)).status_code == 401

    # Лимит исчерпан — дальше 429, даже если пароль вдруг верный.
    blocked = await client.post("/auth/token", data={
        "username": "bruteforced",
        "password": "password123",
    })
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


async def test_successful_logins_are_not_rate_limited(client):
    await _register(client, "frequentflyer")

    correct = {"username": "frequentflyer", "password": "password123"}
    # Успешный вход счётчик не копит: за одним NAT сидят сотни людей,
    # и лимит на все запросы подряд блокировал бы невиновных.
    for _ in range(LOGIN_FAILURE_LIMIT + 5):
        assert (await client.post("/auth/token", data=correct)).status_code == 200


async def test_successful_login_clears_earlier_failures(client):
    await _register(client, "typosquatter")

    wrong = {"username": "typosquatter", "password": "wrong-password"}
    for _ in range(LOGIN_FAILURE_LIMIT - 1):
        assert (await client.post("/auth/token", data=wrong)).status_code == 401

    ok = await client.post("/auth/token", data={
        "username": "typosquatter",
        "password": "password123",
    })
    assert ok.status_code == 200

    # После успеха счётчик обнулён — снова доступен полный запас попыток.
    for _ in range(LOGIN_FAILURE_LIMIT):
        assert (await client.post("/auth/token", data=wrong)).status_code == 401


async def test_rate_limit_counts_per_identifier(fake_redis):
    for _ in range(3):
        await enforce_rate_limit(fake_redis, "login", "1.1.1.1", limit=3, window_seconds=60)

    # Другой IP не наследует счётчик соседа.
    await enforce_rate_limit(fake_redis, "login", "2.2.2.2", limit=3, window_seconds=60)

    with pytest.raises(Exception) as exc_info:
        await enforce_rate_limit(fake_redis, "login", "1.1.1.1", limit=3, window_seconds=60)
    assert exc_info.value.status_code == 429


async def test_oversized_body_rejected_before_parsing(client):
    # Тело не отправляем — важен только заявленный Content-Length: middleware
    # обязан отбить запрос до того, как Starlette начнёт писать его на диск.
    response = await client.post(
        "/users/me/avatar",
        content=b"",
        headers={"Content-Length": str(MAX_REQUEST_BODY_SIZE + 1)},
    )
    assert response.status_code == 413


async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
