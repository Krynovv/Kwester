import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.service.telegram import verify_init_data

TEST_BOT_TOKEN = "123456:TEST-TOKEN"


def _sign(params: dict, bot_token: str) -> str:
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(key=b"WebAppData", msg=bot_token.encode(), digestmod=hashlib.sha256)
    return hmac.new(key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256).hexdigest()


def _build_init_data(bot_token: str, *, auth_date: int, user_id: int = 42) -> str:
    params = {
        "auth_date": str(auth_date),
        "query_id": "test-query-id",
        "user": json.dumps({"id": user_id, "first_name": "Test"}),
    }
    params["hash"] = _sign(params, bot_token)
    return urlencode(params)


@pytest.fixture(autouse=True)
def bot_token(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", SecretStr(TEST_BOT_TOKEN))


def test_accepts_valid_signature():
    init_data = _build_init_data(TEST_BOT_TOKEN, auth_date=int(time.time()))

    result = verify_init_data(init_data)

    assert result is not None
    assert result.user.id == 42


def test_rejects_payload_tampered_after_signing():
    init_data = _build_init_data(TEST_BOT_TOKEN, auth_date=int(time.time()))
    tampered = init_data.replace("Test", "Evil")

    assert verify_init_data(tampered) is None


def test_rejects_signature_from_a_different_token():
    init_data = _build_init_data("999999:OTHER-TOKEN", auth_date=int(time.time()))

    assert verify_init_data(init_data) is None


def test_rejects_stale_auth_date():
    stale = int(time.time()) - 90_000  # старше суток

    init_data = _build_init_data(TEST_BOT_TOKEN, auth_date=stale)

    assert verify_init_data(init_data) is None


def test_returns_none_without_bot_token_configured(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", None)
    init_data = _build_init_data(TEST_BOT_TOKEN, auth_date=int(time.time()))

    assert verify_init_data(init_data) is None
