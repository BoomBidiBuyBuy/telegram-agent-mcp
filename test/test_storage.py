import pytest

import storage
import envs
# import src.storage as storage
# import src.envs as envs


def test_singletone_traits(mocker):
    instance1 = storage.Storage()
    instance2 = storage.Storage()

    assert id(instance1) == id(instance2)


@pytest.mark.parametrize(
    "storage_kind,expected_url",
    [
        (None, "sqlite:///:memory:"),  # default behaviour
        ("mysql", "sqlite:///:memory:"),
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

    storage.Storage()

    storage.create_engine.assert_called_once_with(expected_url, echo=envs.DEBUG_MODE)


def test_session(mocker):
    instance = storage.Storage()

    with instance.build_session():
        pass
