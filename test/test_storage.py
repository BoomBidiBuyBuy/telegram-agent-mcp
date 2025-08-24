import pytest

import storage
# import src.storage as storage
# import src.envs as envs


@pytest.mark.parametrize(
    "storage_kind,expected_url",
    [
        (None, "sqlite:///:memory:"),  # default behaviour
        ("sqlite-memory", "sqlite:///:memory:"),
        ("sqlite", "sqlite:///./dev.db"),
        ("postgres", "postgresql+psycopg2://user:password@host:port/telegram_bot"),
    ],
)
def test_storage_endpoint(mocker, storage_kind, expected_url):
    if storage_kind:
        mocker.patch("envs.STORAGE_DB", storage_kind)
    mocker.patch("envs.PG_USER", "user")
    mocker.patch("envs.PG_PASSWORD", "password")
    mocker.patch("envs.PG_HOST", "host")
    mocker.patch("envs.PG_PORT", "port")

    mocker.patch("storage.create_engine")
    mocker.patch("storage.sessionmaker")

    storage.get_engine_and_sessionmaker()

    if expected_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}

    storage.create_engine.assert_called_once_with(
        expected_url, echo=False, connect_args=connect_args
    )
