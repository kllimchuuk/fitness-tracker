"""Typed, validated environment configuration.

Every environment variable the project reads is declared here, so a wrong or missing value fails at start-up
with a readable message instead of surfacing later as a misbehaving Django setting.
"""

from typing import Annotated

from pydantic import SecretStr
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import NoDecode
from pydantic_settings import SettingsConfigDict


class Env(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        # docker-compose passes `DEBUG: ${DEBUG}`, which is an empty string when the variable is unset
        env_ignore_empty=True,
    )

    secret_key: SecretStr
    debug: bool = False
    # NoDecode: the value is a plain comma-separated string, not JSON
    allowed_hosts: Annotated[list[str], NoDecode] = []

    db_name: str
    db_user: str
    db_password: SecretStr
    db_host: str = "localhost"
    db_port: int = 5432

    csrf_cookie_secure: bool = False
    csrf_cookie_httponly: bool = True
    csrf_cookie_samesite: str = "Strict"
    csrf_trusted_origins: Annotated[list[str], NoDecode] = []

    django_log_level: str = "DEBUG"

    @field_validator("allowed_hosts", "csrf_trusted_origins", mode="before")
    @classmethod
    def _split_commas(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
