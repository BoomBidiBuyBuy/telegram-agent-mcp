from sqlalchemy import Column, Integer, String, ForeignKey, Table, Index
from sqlalchemy.orm import relationship 

import src.storage as storage


Base = storage.Storage.Base


class User(Base):
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


token_action = Table(
    "token_action",
    Base.metadata,
    Column("token_hash", String, ForeignKey("token.id"), primary_key=True),
    Column("action_name", String, ForeignKey("action.name"), primary_key=True),
    Index("ix_token_action_token", "token_hash"),
    Index("ix_token_action_action", "action_name")
)


class Token(Base):
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
    __tablename__ = "action"

    name = Column(String, primary_key=True)

    description = Column(String)

    tokens = relationship(
        "Token",
        secondary=token_action,
        back_populates="actions"
    )
