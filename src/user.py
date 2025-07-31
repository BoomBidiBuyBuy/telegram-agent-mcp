from typing import List

from sqlalchemy import Column, Integer, String, ForeignKey, Table, Index, select
from sqlalchemy.orm import relationship 

import src.storage as storage


Base = storage.Storage.Base


class User(Base):
    """ Defines the `User` table.
   
    An user can have multiple tokens
    """
    __tablename__ = "user"

    id = Column(
        String,
        primary_key=True,
        index=True,
        unique=True
    )

    name = Column(
        String,
        nullable=False
    )

    tokens = relationship(
        "Token",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @staticmethod
    def create(
            user_id: str,
            username: str,
            session: storage.Session
    ) -> 'User':
        user = User(id=user_id, name=username)
        session.add(user)
        return user

    @staticmethod
    def find_by_id(
        user_id: str,
        session: storage.Session
    ) -> List['User']:
        return session.query(User).filter_by(id=user_id).all()

    @staticmethod
    def find_by_name(
        name: str,
        session: storage.Session
    ) -> List['User']:
        return session.query(User).filter_by(name=name).all()

    @staticmethod
    def exists(
        user_id: str,
        session: storage.Session
    ) -> bool:
        return session.query(select(User).filter_by(id=user_id).exists()).scalar()


# Association between token and actions
# Without it we would need to create the same actions per different tokens
# because removing tokens would be removing corresponding action.
token_action = Table(
    "token_action",
    Base.metadata,
    Column("token_hash", String, ForeignKey("token.id"), primary_key=True),
    Column("action_name", String, ForeignKey("action.name"), primary_key=True),
    Index("ix_token_action_token", "token_hash"),
    Index("ix_token_action_action", "action_name")
)


class Token(Base):
    """ Defines the `Token` table.
    It contains access (welcome) tokens that we share with
    our users to work with API.

    Every token can have multiple actions.
    They are bound using the `token_action` association.
    """

    __tablename__ = "token"

    id = Column(String, primary_key=True, index=True, unique=True)

    user_id = Column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    user = relationship(
        "User",
        back_populates="tokens"
    )

    actions = relationship(
        "Action",
        secondary=token_action,
        back_populates="tokens",
    )


class Action(Base):
    """ Defines the `Action` table.
    It contains action we is allowed an user can perform according to a token.
    """

    __tablename__ = "action"

    name = Column(String, primary_key=True)

    description = Column(String)

    tokens = relationship(
        "Token",
        secondary=token_action,
        back_populates="actions"
    )
