import logging

from typing import Union

from sqlalchemy import Column, Integer, String, ForeignKey, Table, Index, select
from sqlalchemy.orm import relationship

from storage import Base


logger = logging.getLogger(__name__)


class AuthUser(Base):
    """Defines the `AuthUser` table.

    An user can have multiple tokens
    """

    __tablename__ = "auth_user"

    id = Column(String, primary_key=True, index=True, unique=True)

    name = Column(String, nullable=False)

    tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")

    @staticmethod
    def create(user_id: str, username: str, session) -> "AuthUser":
        logger.info(f"Create a new user user_id={user_id}, name={username}")
        user = AuthUser(id=user_id, name=username)
        session.add(user)
        session.commit()
        return user

    @staticmethod
    def find_by_id(user_id: str, session) -> Union["AuthUser", None]:
        """Finds a user by user id.
        Returns user or `None` because user id is index
        """
        return session.query(AuthUser).filter_by(id=user_id).one_or_none()

    @staticmethod
    def exists(user_id: str, session) -> bool:
        """Checks whether user with corresponding user id exists or not"""
        return session.query(select(AuthUser).filter_by(id=user_id).exists()).scalar()

    def revoke_token(self, token: str, session) -> bool:
        """Method revokes (remove) token from a current user"""
        logger.info(f"Revoke {token}")

        token = AuthToken.find_by_id(token, session)

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
    Column("token_hash", String, ForeignKey("auth_token.id"), primary_key=True),
    Column("action_name", String, ForeignKey("auth_action.name"), primary_key=True),
    Index("ix_token_action_token", "token_hash"),
    Index("ix_token_action_action", "action_name"),
)


class AuthToken(Base):
    """Defines the `Token` table.
    It contains access (welcome) tokens that we share with
    our users to work with API.

    Every token can have multiple actions.
    They are bound using the `token_action` association.
    """

    __tablename__ = "auth_token"

    id = Column(String, primary_key=True, index=True, unique=True)

    # TODO: Do we really need it?
    user_id = Column(Integer, ForeignKey("auth_user.id"), index=True)

    user = relationship("AuthUser", back_populates="tokens")

    actions = relationship(
        "AuthAction",
        secondary=token_action,
        back_populates="tokens",
    )

    @staticmethod
    def create(id: str, session) -> "AuthToken":
        logger.info(f"Create a new token id='{id}'")
        token = AuthToken(id=id)
        session.add(token)
        session.commit()
        return token

    @staticmethod
    def exists(token: str, session) -> bool:
        """Checks whether passed token exists or not.

        Can be used for tokens valdation.
        """
        return session.query(select(AuthToken).filter_by(id=token).exists()).scalar()

    @staticmethod
    def find_by_id(token: str, session) -> Union["AuthToken", None]:
        """Finds a token"""
        return session.query(AuthToken).filter_by(id=token).one_or_none()


class AuthAction(Base):
    """Defines the `Action` table.
    It contains action we is allowed an user can perform according to a token.
    """

    __tablename__ = "auth_action"

    name = Column(String, primary_key=True)

    description = Column(String)

    tokens = relationship("AuthToken", secondary=token_action, back_populates="actions")
