from datetime import datetime

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.redis import get_redis


class FakeRedis:
    """Заглушка Redis на обычном словаре — живой сервер тестам не нужен.

    Кэширует по-настоящему: иначе тесты не проверяли бы инвалидацию
    в invalidate_boss_status и не ловили бы протухший статус после боя.
    TTL (ex) игнорируется — истечение по времени здесь не воспроизводится.
    """

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def get(self, key):
        return self._data.get(key)

    async def set(self, key, value, ex=None):
        self._data[key] = value

    async def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)

    async def incr(self, key):
        value = int(self._data.get(key, 0)) + 1
        self._data[key] = str(value)
        return value

    async def expire(self, key, seconds):
        return key in self._data

    async def ttl(self, key):
        # Реальный TTL не моделируется; -1 = «ключ есть, срок не истекает».
        return -1 if key in self._data else -2


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest.fixture
def freeze_time(monkeypatch):
    """Останавливает часы во всех модулях, которые их читают.

    Момент задаётся в UTC, а now(tz) отдаёт его пересчитанным в запрошенный
    пояс. Возвращать UTC-время с чужим ярлыком пояса нельзя: логика локальных
    суток именно на этом пересчёте и держится.
    """

    def _freeze(moment: datetime):
        class FrozenDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is None:
                    return moment.replace(tzinfo=None)
                return moment.astimezone(tz)

        import app.core.timezones as timezones_module
        import app.service.boss as boss_module
        import app.service.quest as quest_module

        for module in (timezones_module, quest_module, boss_module):
            # raising=False: boss.py больше не читает datetime.now() напрямую
            # (всё через core.timezones), так что там нет своего атрибута
            # datetime на уровне модуля — патчить нечего, но и не ошибка.
            monkeypatch.setattr(module, "datetime", FrozenDatetime, raising=False)
        return FrozenDatetime

    return _freeze


engine = create_async_engine(settings.test_database_url)
TestSession = async_sessionmaker(engine, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest.fixture
async def db_session():
    async with TestSession() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))

@pytest.fixture
def session_factory():
    """Для кода, открывающего собственную сессию (не через Depends(get_db)) —
    сейчас только send_due_habit_reminders, первая проактивная (не по запросу)
    задача в проекте. Данные, нужные такому коду, должны быть закоммичены
    через db_session, а не просто flush — иначе новая сессия их не увидит."""
    return TestSession

@pytest.fixture
async def client(db_session, fake_redis):
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
