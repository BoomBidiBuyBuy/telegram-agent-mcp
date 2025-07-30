import pytest

import src.storage as storage


def test_singletone_traits(mocker):
    mocker.patch("src.envs.STORAGE_DB", "mysql")

    instance1 = storage.Storage()
    instance2 = storage.Storage()

    assert id(instance1) == id(instance2)


@pytest.mark.parametrize(
    "storage_kind,expected_url",
    [
        ("mysql", "sqlite:///:memory:"),
        ("postgres", "postgresql+psycopg2://user:password@host:port/telegram_bot"),
    ],
)
def test_storage_endpoint(mocker, storage_kind, expected_url):
    mocker.patch("src.envs.STORAGE_DB", storage_kind)
    mocker.patch("src.envs.PG_USER", "user")
    mocker.patch("src.envs.PG_PASSWORD", "password")
    mocker.patch("src.envs.PG_HOST", "host")
    mocker.patch("src.envs.PG_PORT", "port")

    mocker.patch("src.storage.create_engine")

    storage.Storage()

    storage.create_engine.assert_called_once_with(expected_url)


def test_session(mocker):
    mocker.patch("src.envs.STORAGE_DB", "mysql")

    instance = storage.Storage()

    assert instance.session is not None
