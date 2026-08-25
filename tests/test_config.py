import os
from unittest.mock import patch

import pytest

from app.cofigurations.config import Configuration


def _patched_getenv(missing_key: str):
    real_getenv = os.getenv

    def fake_getenv(key: str, default: str | None = None) -> str | None:
        if key == missing_key:
            return None
        return real_getenv(key, default)

    return fake_getenv


def test_missing_db_connection_string_raises_friendly_error() -> None:
    with patch("app.cofigurations.config.os.getenv", side_effect=_patched_getenv("DB_CONNECTION_STRING")):
        with pytest.raises(RuntimeError, match="DB_CONNECTION_STRING"):
            Configuration()


def test_missing_jwt_secret_raises_friendly_error() -> None:
    with patch("app.cofigurations.config.os.getenv", side_effect=_patched_getenv("JWT_SECRET")):
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            Configuration()
