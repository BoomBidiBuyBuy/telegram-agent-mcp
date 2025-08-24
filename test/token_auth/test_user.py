import pytest

from sqlalchemy import select

from storage import SessionLocal, init_db, engine, Base
from token_auth_db.models import AuthUser, AuthToken, AuthAction


@pytest.fixture
def session():
    with SessionLocal() as session:
        yield session

    # need to drop all tables after each test
    # and re-create them
    # otherwise data from previous test will be
    # present in the next test
    Base.metadata.drop_all(bind=engine)
    init_db(engine)


def test_user(session):
    """Check that the User table functioning without errors"""

    AuthUser.create(user_id="tgabcd", username="Alice", session=session)
    AuthUser.create(user_id="tg1234", username="Bob", session=session)
    session.commit()

    user = AuthUser.find_by_id("tgabcd", session)
    assert user.name == "Alice"

    user = AuthUser.find_by_id("tgxxxx", session)
    assert user is None

    assert AuthUser.exists("tg1234", session)
    assert not AuthUser.exists("tg5678", session)


def test_token(session):
    """Check that the Token table functioning without errors"""
    user1 = AuthUser(id="tgabcd", name="Alice")
    user2 = AuthUser(id="tg1234", name="Bob")

    AuthToken(id="token123", user=user1)
    AuthToken(id="token345", user=user1)
    AuthToken(id="token567", user=user2)

    session.add_all([user1, user2])
    session.commit()

    alice = AuthUser.find_by_id("tgabcd", session)
    bob = AuthUser.find_by_id("tg1234", session)

    alice_tokens = {token.id for token in alice.tokens}
    bob_tokens = {token.id for token in bob.tokens}

    assert {"token123", "token345"} == alice_tokens
    assert {"token567"} == bob_tokens

    # revoke token
    assert len(bob.tokens) == 1 and bob.tokens[0].id == "token567"

    assert bob.revoke_token("token567", session)  # returns true in success
    session.commit()

    bob = AuthUser.find_by_id("tg1234", session)
    assert len(bob.tokens) == 0

    assert not bob.revoke_token("token567", session)  # already revoken


def test_standalone_token(session):
    """Check case creating tokens without users.
    This case is important when we issue an token when we
    do not know the user yet"""

    # check that token not yet created
    assert not AuthToken.exists("token123", session)

    # check token creation
    token = AuthToken(id="token123")

    session.add_all([token])
    session.commit()

    assert AuthToken.exists("token123", session)

    # check assigning user to a token
    token = AuthToken.find_by_id("token123", session)
    user = AuthUser(id="tg1234", name="Alice")

    token.user = user
    session.commit()

    assert AuthUser.find_by_id("tg1234", session).tokens[0].id == "token123"


def test_action(session):
    """Checks that:
    - actions can be added
    - actions cen be removed
    - token revokation also remove corresponding actions from users abilities
    """
    user1 = AuthUser(id="tgabcd", name="Alice")
    user2 = AuthUser(id="tg1234", name="Bob")

    token1 = AuthToken(id="token123", user=user1)
    token2 = AuthToken(id="token345", user=user1)
    token3 = AuthToken(id="token567", user=user2)

    action_pg_read = AuthAction(
        name="postgres_read", description="Postgres read access"
    )
    action_pg_write = AuthAction(
        name="postgres_write", description="Postgres write access"
    )
    action_airflow_read = AuthAction(name="airflow_read", description="Airflow read")

    token1.actions.extend([action_pg_read, action_pg_write])
    token2.actions.append(action_airflow_read)
    token3.actions.append(action_pg_read)

    session.add_all([user1, user2])
    session.commit()

    # whether user has action
    stmt = (
        select(AuthToken)
        .join(AuthToken.user)
        .join(AuthToken.actions)
        .where(AuthUser.id == "tg1234", AuthAction.name == "airflow_read")
        .limit(1)
    )

    assert session.execute(stmt).scalar_one_or_none() is None

    ####################
    # Add action for Bob
    ####################
    token = (
        session.query(AuthToken)
        .filter_by(user_id="tg1234", id="token567")
        .one_or_none()
    )
    token.actions.append(action_airflow_read)
    session.commit()

    assert session.execute(stmt).scalar_one_or_none() is not None

    ################
    # Remove action
    ################
    action = session.query(AuthAction).filter_by(name="airflow_read").one_or_none()
    token.actions.remove(action)
    session.commit()

    assert session.execute(stmt).scalar_one_or_none() is None

    ################
    # Revoke token
    ################

    # check initial state
    stmt = (
        select(AuthAction)
        .join(AuthToken.actions)
        .join(AuthToken.user)
        .where(AuthToken.user_id == "tgabcd")
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
        select(AuthAction)
        .join(AuthToken.actions)
        .join(AuthToken.user)
        .where(AuthToken.user_id == "tg1234")
        .distinct()
    )

    actions = session.execute(stmt).scalars().all()

    assert {"postgres_read"} == {action.name for action in actions}
