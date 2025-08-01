import logging

from typing import Union

from sqlalchemy import Column, Integer, String, ForeignKey, Table, Index, select
from sqlalchemy.orm import relationship

import storage


logger = logging.getLogger(__name__)


Base = storage.Storage.Base


class User(Base):
    """Defines the `User` table.

    An user can have multiple tokens
    """

    __tablename__ = "user"

    id = Column(String, primary_key=True, index=True, unique=True)

    name = Column(String, nullable=False)

    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")

    @staticmethod
    def create(user_id: str, username: str, session: storage.Session) -> "User":
        logger.info(f"Create a new user user_id={user_id}, name={username}")
        user = User(id=user_id, name=username)
        session.add(user)
        return user

    @staticmethod
    def find_by_id(user_id: str, session: storage.Session) -> Union["User", None]:
        """Finds a user by user id.
        Returns user or `None` because user id is index
        """
        return session.query(User).filter_by(id=user_id).one_or_none()

    #    @staticmethod
    #    def find_by_name(
    #        name: str,
    #        session: storage.Session
    #    ) -> List['User']:
    #        """ Finds users by name.
    #        Returns list of users because name is not unique
    #        """
    #        return session.query(User).filter_by(name=name).all()

    @staticmethod
    def exists(user_id: str, session: storage.Session) -> bool:
        """Checks whether user with corresponding user id exists or not"""
        return session.query(select(User).filter_by(id=user_id).exists()).scalar()

    def revoke_token(self, token: str, session: storage.Session) -> bool:
        """Method revokes (remove) token from a current user"""
        logger.info(f"Revoke {token}")

        token = Token.find_by_id(token, session)

        if token:
            session.delete(token)
            return True
        else:
            logger.info(f"Try to revoke {token} that is not found")
            return False


# Association between token and actions
# Without it we would need to create the same actions per different tokens
# because removing tokens would be removing corresponding action.
token_action = Table(
    "token_action",
    Base.metadata,
    Column("token_hash", String, ForeignKey("token.id"), primary_key=True),
    Column("action_name", String, ForeignKey("action.name"), primary_key=True),
    Index("ix_token_action_token", "token_hash"),
    Index("ix_token_action_action", "action_name"),
)


class Token(Base):
    """Defines the `Token` table.
    It contains access (welcome) tokens that we share with
    our users to work with API.

    Every token can have multiple actions.
    They are bound using the `token_action` association.
    """

    __tablename__ = "token"

    id = Column(String, primary_key=True, index=True, unique=True)

    # TODO: Do we really need it?
    user_id = Column(Integer, ForeignKey("user.id"), index=True)

    user = relationship("User", back_populates="tokens")

    actions = relationship(
        "Action",
        secondary=token_action,
        back_populates="tokens",
    )

    @staticmethod
    def create(id: str, session: storage.Session) -> "User":
        logger.info(f"Create a new token id='{id}'")
        token = Token(id=id)
        session.add(token)
        return token

    @staticmethod
    def exists(token: str, session: storage.Session) -> bool:
        """Checks whether passed token exists or not.

        Can be used for tokens valdation.
        """
        return session.query(select(Token).filter_by(id=token).exists()).scalar()

    @staticmethod
    def find_by_id(token: str, session: storage.Session) -> Union["Token", None]:
        """Finds a token"""
        return session.query(Token).filter_by(id=token).one_or_none()


class Action(Base):
    """Defines the `Action` table.
    It contains action we is allowed an user can perform according to a token.
    """

    __tablename__ = "action"

    name = Column(String, primary_key=True)

    description = Column(String)

    tokens = relationship("Token", secondary=token_action, back_populates="actions")
