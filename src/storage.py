import envs

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


storage_url = None

if envs.STORAGE_DB == "mysql":
    storage_url = "sqlite:///:memory:"
elif envs.STORAGE_DB == "postgres":
    storage_url = f"postgresql+psycopg2://{envs.PG_USER}:{envs.PG_PASSWORD}@{envs.PG_HOST}:{envs.PG_PORT}/telegram_bot"
else:
    raise ValueError("The `STORAGE_DB` env variable is not correct")


engine = create_engine(storage_url)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
