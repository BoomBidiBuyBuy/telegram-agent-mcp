import pytest

from sqlalchemy import select

from src.storage import Storage
from src.user import User, Token


@pytest.fixture
def storage():
    return Storage()


@pytest.fixture
def session(storage):
    with storage.make_session() as session:
        yield session;


def test_user(session):
    user1 = User(telegram_id="tgabcd", name="Alice")
    user2 = User(telegram_id="tg1234", name="Bob")
    session.add_all([user1, user2])

    assert session.query(
        select(User).filter_by(telegram_id="tgabcd").exists()
    ).scalar()

    assert not session.query(
        select(User).filter_by(telegram_id="tgxxxx").exists()
    ).scalar()

    assert session.query(
        select(User).filter_by(name="Bob").exists()
    ).scalar()


def test_token(session):
    user1 = User(telegram_id="tgabcd", name="Alice")
    user2 = User(telegram_id="tg1234", name="Bob")

    token1 = Token(token="token123", user=user1)
    token2 = Token(token="token345", user=user1)
    token3 = Token(token="token567", user=user2)

    session.add_all([user1, user2])

    alice = session.query(User).filter_by(name="Alice").one_or_none()
    bob = session.query(User).filter_by(name="Bob").one_or_none()

    alice_tokens = { token.token for token in alice.tokens }
    bob_tokens = { token.token for token in bob.tokens }

    assert {"token123", "token345"} == alice_tokens
    assert {"token567"} == bob_tokens
