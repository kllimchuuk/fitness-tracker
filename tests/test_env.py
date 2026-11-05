import pytest
from pydantic import ValidationError

from config.env import Env

REQUIRED = {"SECRET_KEY": "s3cret", "DB_NAME": "db", "DB_USER": "user", "DB_PASSWORD": "pw"}


@pytest.fixture
def clean_env(monkeypatch):
    for name in (*REQUIRED, "DEBUG", "ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS", "DB_HOST", "DB_PORT"):
        monkeypatch.delenv(name, raising=False)
    for name, value in REQUIRED.items():
        monkeypatch.setenv(name, value)
    return monkeypatch


def load() -> Env:
    return Env(_env_file=None)


@pytest.mark.parametrize(("raw", "expected"), [("False", False), ("false", False), ("0", False), ("True", True), ("1", True)])
def test_debug_is_parsed_as_bool(clean_env, raw, expected):
    clean_env.setenv("DEBUG", raw)

    assert load().debug is expected


def test_debug_defaults_to_false_when_unset_or_empty(clean_env):
    assert load().debug is False

    clean_env.setenv("DEBUG", "")

    assert load().debug is False


def test_missing_secret_key_fails_fast(clean_env):
    clean_env.delenv("SECRET_KEY")

    with pytest.raises(ValidationError, match="secret_key"):
        load()


def test_secret_is_masked_in_repr(clean_env):
    assert "s3cret" not in repr(load())


def test_comma_separated_lists(clean_env):
    clean_env.setenv("ALLOWED_HOSTS", "a.example, b.example,")
    clean_env.setenv("CSRF_TRUSTED_ORIGINS", "https://a.example")

    env = load()

    assert env.allowed_hosts == ["a.example", "b.example"]
    assert env.csrf_trusted_origins == ["https://a.example"]


def test_lists_default_to_empty(clean_env):
    env = load()

    assert env.allowed_hosts == []
    assert env.csrf_trusted_origins == []


def test_database_defaults(clean_env):
    env = load()

    assert env.db_host == "localhost"
    assert env.db_port == 5432
