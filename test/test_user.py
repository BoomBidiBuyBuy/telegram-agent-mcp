import pytest

from sqlalchemy import select

from storage import Storage
from user import User, Token, Action


@pytest.fixture
def storage():
    return Storage()


@pytest.fixture
def session(storage):
    with storage.build_session() as session:
        yield session


def test_user(session):
    """Check that the User table functioning without errors"""

    User.create("tgabcd", "Alice", session)
    User.create("tg1234", "Bob", session)
    session.commit()

    user = User.find_by_id("tgabcd", session)
    assert user.name == "Alice"

    user = User.find_by_id("tgxxxx", session)
    assert user is None

    assert User.exists("tg1234", session)
    assert not User.exists("tg5678", session)


def test_token(session):
    """Check that the Token table functioning without errors"""
    user1 = User(id="tgabcd", name="Alice")
    user2 = User(id="tg1234", name="Bob")

    Token(id="token123", user=user1)
    Token(id="token345", user=user1)
    Token(id="token567", user=user2)

    session.add_all([user1, user2])
    session.commit()

    alice = User.find_by_id("tgabcd", session)
    bob = User.find_by_id("tg1234", session)

    alice_tokens = {token.id for token in alice.tokens}
    bob_tokens = {token.id for token in bob.tokens}

    assert {"token123", "token345"} == alice_tokens
    assert {"token567"} == bob_tokens

    # revoke token
    assert len(bob.tokens) == 1 and bob.tokens[0].id == "token567"

    assert bob.revoke_token("token567", session)  # returns true in success
    session.commit()

    bob = User.find_by_id("tg1234", session)
    assert len(bob.tokens) == 0

    assert not bob.revoke_token("token567", session)  # already revoken


def test_standalone_token(session):
    """Check case creating tokens without users.
    This case is important when we issue an token when we
    do not know the user yet"""

    # check that token not yet created
    assert not Token.exists("token123", session)

    # check token creation
    token = Token(id="token123")

    session.add_all([token])
    session.commit()

    assert Token.exists("token123", session)

    # check assigning user to a token
    token = Token.find_by_id("token123", session)
    user = User(id="tg1234", name="Alice")

    token.user = user
    session.commit()

    assert User.find_by_id("tg1234", session).tokens[0].id == "token123"


def test_action(session):
    """Checks that:
    - actions can be added
    - actions cen be removed
    - token revokation also remove corresponding actions from users abilities
    """
    user1 = User(id="tgabcd", name="Alice")
    user2 = User(id="tg1234", name="Bob")

    token1 = Token(id="token123", user=user1)
    token2 = Token(id="token345", user=user1)
    token3 = Token(id="token567", user=user2)

    action_pg_read = Action(name="postgres_read", description="Postgres read access")
    action_pg_write = Action(name="postgres_write", description="Postgres write access")
    action_airflow_read = Action(name="airflow_read", description="Airflow read")

    token1.actions.extend([action_pg_read, action_pg_write])
    token2.actions.append(action_airflow_read)
    token3.actions.append(action_pg_read)

    session.add_all([user1, user2])
    session.commit()

    # whether user has action
    stmt = (
        select(Token)
        .join(Token.user)
        .join(Token.actions)
        .where(User.id == "tg1234", Action.name == "airflow_read")
        .limit(1)
    )

    assert session.execute(stmt).scalar_one_or_none() is None

    ####################
    # Add action for Bob
    ####################
    token = (
        session.query(Token).filter_by(user_id="tg1234", id="token567").one_or_none()
    )
    token.actions.append(action_airflow_read)
    session.commit()

    assert session.execute(stmt).scalar_one_or_none() is not None

    ################
    # Remove action
    ################
    action = session.query(Action).filter_by(name="airflow_read").one_or_none()
    token.actions.remove(action)
    session.commit()

    assert session.execute(stmt).scalar_one_or_none() is None

    ################
    # Revoke token
    ################

    # check initial state
    stmt = (
        select(Action)
        .join(Token.actions)
        .join(Token.user)
        .where(Token.user_id == "tgabcd")
        .distinct()
    )

    actions = session.execute(stmt).scalars().all()

    assert {"postgres_read", "postgres_write", "airflow_read"} == {
        action.name for action in actions
    }

    # check after removal state
    user1.revoke_token("token123", session)
    session.commit()

    actions = session.execute(stmt).scalars().all()

    assert {"airflow_read"} == {action.name for action in actions}

    # check that Bob still able to tun 'postgres_read'
    stmt = (
        select(Action)
        .join(Token.actions)
        .join(Token.user)
        .where(Token.user_id == "tg1234")
        .distinct()
    )

    actions = session.execute(stmt).scalars().all()

    assert {"postgres_read"} == {action.name for action in actions}
