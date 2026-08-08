"""Тесты на сам клиент Redis, а не на код, который им пользуется.

Во всех остальных тестах Redis подменён заглушкой FakeRedis, поэтому
настоящий клиент не выполняется никогда. А from_url молча принимает
неизвестные kwargs и падает только при первом реальном обращении —
такая ошибка доезжает до прода живой (опечатка decode_responce вместо
decode_responses роняла /boss/status в 500).
"""

from app.core.redis import redis_client


def test_client_decodes_responses():
    kwargs = redis_client.connection_pool.connection_kwargs
    assert kwargs.get("decode_responses") is True


def test_connection_kwargs_are_accepted_by_driver():
    """Собираем соединение (без сети) — так неизвестные параметры всплывают
    сразу, а не при первом запросе к боссу."""
    pool = redis_client.connection_pool
    connection = pool.make_connection()
    assert connection is not None
