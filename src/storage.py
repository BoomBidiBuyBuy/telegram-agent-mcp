import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import src.envs as envs


logger = logging.getLogger(__name__)


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
            logger.warning(
                "The `mysql` is used as storage db! Use it ONLY for development"
            )
        elif envs.STORAGE_DB == "postgres":
            endpoint = f"postgresql+psycopg2://{envs.PG_USER}:{envs.PG_PASSWORD}@{envs.PG_HOST}:{envs.PG_PORT}/telegram_bot"
            logger.info("The `postgres` is used as storage db")
        else:
            raise ValueError("The `STORAGE_DB` env variable is not correct")

        self._engine = create_engine(endpoint)
        self._session = None

    @property
    def session(self):
        """Build a session on-demand"""
        if self._session is None:
            logger.info("Session has not been created, create it")
            Storage.Base.metadata.create_all(self._engine)

            Session = sessionmaker(bind=self._engine)
            self._session = Session()

        return self._session
