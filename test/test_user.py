import pytest

from sqlalchemy import select

from src.storage import Storage
from src.user import User, Token


@pytest.fixture
def storage():
    return Storage()


def test_add(storage):
    with storage.make_session() as session:
        user1 = User(telegram_id="abcdef", name="Alice")
        session.add_all([user1])

    with storage.make_session() as session:
        assert session.query(
            select(User).filter_by(telegram_id="abcdef").exists()
        ).scalar()
