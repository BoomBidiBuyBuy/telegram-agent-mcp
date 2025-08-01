import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import src.envs as envs


logger = logging.getLogger(__name__)


class Session:
    def __init__(self, engine):
        Storage.Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        self._session = Session()

    def __enter__(self):
        return self._session

    def __exit__(self, *args, **kwargs):
        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
        finally:
            self._session.close()


class Storage:
    _instance = None

    Base = declarative_base()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        endpoint = None

        if envs.STORAGE_DB == "mysql":
            endpoint = "sqlite:///:memory:"

            if not envs.DEBUG_MODE:
                logger.warning(
                    "The `mysql` is used as storage db! Use it ONLY for development"
                )
        elif envs.STORAGE_DB == "postgres":
            endpoint = f"postgresql+psycopg2://{envs.PG_USER}:{envs.PG_PASSWORD}@{envs.PG_HOST}:{envs.PG_PORT}/telegram_bot"
            logger.info("The `postgres` is used as storage db")
        else:
            raise ValueError("The `STORAGE_DB` env variable is not correct")

        self._engine = create_engine(endpoint, echo=envs.DEBUG_MODE)

    def make_session(self) -> Session:
        return Session(self._engine)
