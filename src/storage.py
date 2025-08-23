import envs
import logging
from typing import Callable, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def build_database_url() -> str:
    if envs.STORAGE_DB == "mysql":
        if not envs.DEBUG_MODE:
            logger.warning(
                "The `mysql` is used as storage db! Use it ONLY for development"
            )
        return "sqlite:///:memory:"
        #return "sqlite:///./dev.db"
    elif envs.STORAGE_DB == "postgres":
        logger.info("The `postgres` is used as storage db")
        return f"postgresql+psycopg2://{envs.PG_USER}:{envs.PG_PASSWORD}@{envs.PG_HOST}:{envs.PG_PORT}/telegram_bot"
    else:
        raise ValueError("The `STORAGE_DB` env variable is not correct")



def get_engine_and_sessionmaker() -> Tuple[object, sessionmaker]:
    database_url = build_database_url()
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(database_url, echo=False, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine, SessionLocal


def init_db(engine) -> None:
    from token_auth_db.models import AuthUser, AuthToken, AuthAction  # noqa: F401 - import to register models
    from user_group_db.models import Group, User  # noqa: F401 - import to register models

    Base.metadata.create_all(bind=engine)


def get_db_session(SessionLocal: sessionmaker) -> Callable:
    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    return _get_db



engine, SessionLocal = get_engine_and_sessionmaker()
init_db(engine)
get_db = get_db_session(SessionLocal)