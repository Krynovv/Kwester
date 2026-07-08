import pytest
from fastapi import HTTPException

from app.models.user import User
from app.models.reward import Reward
from app.core.auth import hash_password
from app.service.economy import purchase_reward


@pytest.fixture
async def user(db_session):
    u = User(username="buyer", email="buyer@test.com", password_hash=hash_password("password123"), currency_balance=20)
    db_session.add(u)
    await db_session.flush()
    return u


async def test_purchase_reward_deducts_balance(db_session, user):
    reward = Reward(user_id=user.id, title="test reward", cost=10)
    db_session.add(reward)
    await db_session.flush()

    result = await purchase_reward(db_session, user.id, reward.id)

    assert result.is_purchased is True
    await db_session.refresh(user)
    assert user.currency_balance == 10


async def test_purchase_reward_insufficient_balance(db_session, user):
    reward = Reward(user_id=user.id, title="expensive", cost=999)
    db_session.add(reward)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await purchase_reward(db_session, user.id, reward.id)
    assert exc_info.value.status_code == 400

    await db_session.refresh(user)
    assert user.currency_balance == 20  # баланс не изменился


async def test_cannot_purchase_reward_twice(db_session, user):
    reward = Reward(user_id=user.id, title="one time", cost=5)
    db_session.add(reward)
    await db_session.flush()

    await purchase_reward(db_session, user.id, reward.id)

    with pytest.raises(HTTPException) as exc_info:
        await purchase_reward(db_session, user.id, reward.id)
    assert exc_info.value.status_code == 400


async def test_purchase_other_users_reward_returns_404(db_session, user):
    other = User(username="other2", email="other2@test.com", password_hash=hash_password("password123"))
    db_session.add(other)
    await db_session.flush()

    reward = Reward(user_id=other.id, title="not yours", cost=5)
    db_session.add(reward)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await purchase_reward(db_session, user.id, reward.id)
    assert exc_info.value.status_code == 404
