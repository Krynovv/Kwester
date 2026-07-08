import pytest

from app.models.user import User
from app.models.stat import Stat
from app.core.auth import hash_password, verify_password, create_access_token, verify_access_token
from sqlalchemy import select


async def test_register_creates_user(client):
    response = await client.post("/auth/register", json={
        "username": "newuser",
        "email": "newuser@test.com",
        "password": "password123",
    })

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "password" not in data          # пароль не должен утекать в ответе
    assert "password_hash" not in data     # хэш пароля тоже не должен утекать


async def test_register_creates_default_stats(client, db_session):
    response = await client.post("/auth/register", json={
        "username": "statuser",
        "email": "statuser@test.com",
        "password": "password123",
    })
    user_id = response.json()["id"]

    result = await db_session.execute(select(Stat).where(Stat.user_id == user_id))
    stats = result.scalars().all()

    assert len(stats) == 5   # или сколько у тебя в DEFAULT_STATS
    assert all(stat.level == 1 for stat in stats)
    assert all(stat.current_xp == 0 for stat in stats)


async def test_register_duplicate_email_fails(client):
    payload = {"username": "dup1", "email": "dup@test.com", "password": "password123"}
    await client.post("/auth/register", json=payload)

    payload2 = {"username": "dup2", "email": "dup@test.com", "password": "password123"}
    response = await client.post("/auth/register", json=payload2)

    assert response.status_code == 400


async def test_register_short_password_rejected(client):
    response = await client.post("/auth/register", json={
        "username": "shortpass",
        "email": "shortpass@test.com",
        "password": "short",   # меньше min_length=8
    })

    assert response.status_code == 422   # ошибка валидации Pydantic


async def test_login_success(client):
    await client.post("/auth/register", json={
        "username": "loginuser",
        "email": "loginuser@test.com",
        "password": "password123",
    })

    response = await client.post("/auth/token", data={
        "username": "loginuser",
        "password": "password123",
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password_fails(client):
    await client.post("/auth/register", json={
        "username": "wrongpass",
        "email": "wrongpass@test.com",
        "password": "password123",
    })

    response = await client.post("/auth/token", data={
        "username": "wrongpass",
        "password": "incorrect",
    })

    assert response.status_code == 401


async def test_login_nonexistent_user_fails(client):
    response = await client.post("/auth/token", data={
        "username": "ghost",
        "password": "whatever123",
    })

    assert response.status_code == 401


async def test_protected_endpoint_without_token_fails(client):
    response = await client.get("/stats")
    assert response.status_code == 401


async def test_protected_endpoint_with_valid_token(client):
    await client.post("/auth/register", json={
        "username": "protecteduser",
        "email": "protecteduser@test.com",
        "password": "password123",
    })
    login = await client.post("/auth/token", data={
        "username": "protecteduser",
        "password": "password123",
    })
    token = login.json()["access_token"]

    response = await client.get("/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


# --- юнит-тесты на чистые функции security, без похода в БД ---

def test_hash_password_and_verify():
    hashed = hash_password("mypassword123")
    assert hashed != "mypassword123"           # пароль реально хэшируется, не хранится как есть
    assert verify_password("mypassword123", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_access_token_roundtrip():
    token = create_access_token(data={"sub": "42"})
    user_id = verify_access_token(token)
    assert user_id == "42"


def test_invalid_token_returns_none():
    assert verify_access_token("совершенно.невалидный.токен") is None
