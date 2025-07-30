from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship 

import src.storage as storage


Base = storage.Storage.Base


class User(Base):
    __tablename__ = "user"

    telegram_id = Column(
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


class Token(Base):
    __tablename__ = "token"

    token = Column(String, primary_key=True, index=True, unique=True)

    user_id = Column(
        Integer,
        ForeignKey("user.telegram_id"),
        nullable=False,
        index=True
    )

    user = relationship(
        "User",
        back_populates="tokens"
    )

    actions = relationship(
        "Action",
        back_populates="tokens",
        cascade="all, delete-orphan"
    )


class Action(Base):
    __tablename__ = "action"

    id = Column(Integer, primary_key=True)

    token_id = Column(
        String,
        ForeignKey("token.token"),
        nullable=False,
        index=True
    )

    name = Column(String)

    description = Column(String)

    tokens = relationship(
        "Token",
        back_populates="actions"
    )
