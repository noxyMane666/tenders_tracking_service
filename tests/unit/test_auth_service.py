import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.cofigurations.auth_settings import AuthSettings
from app.exceptions.domain_exceptions import InvalidAuthTokenException
from app.services.auth_service import JwtAuthService

SECRET = "test-secret"
ALGORITHM = "HS256"


@pytest.fixture
def auth_service() -> JwtAuthService:
    settings = AuthSettings(JWT_SECRET=SECRET, JWT_ALGORITHM=ALGORITHM, JWT_USER_ID_CLAIM="sub")
    return JwtAuthService(settings)


def make_token(
        secret: str = SECRET,
        algorithm: str = ALGORITHM,
        exp_delta: timedelta | None = timedelta(minutes=5),
        **claims
) -> str:
    payload = dict(claims)
    if exp_delta is not None:
        payload["exp"] = datetime.now(timezone.utc) + exp_delta
    return jwt.encode(payload, secret, algorithm=algorithm)


def test_valid_token_returns_user_id(auth_service: JwtAuthService) -> None:
    user_id = uuid.uuid4()
    token = make_token(sub=str(user_id))

    result = auth_service.get_current_user_id(token)

    assert result == user_id


def test_expired_token_raises(auth_service: JwtAuthService) -> None:
    token = make_token(sub=str(uuid.uuid4()), exp_delta=timedelta(minutes=-5))

    with pytest.raises(InvalidAuthTokenException):
        auth_service.get_current_user_id(token)


def test_wrong_signature_raises(auth_service: JwtAuthService) -> None:
    token = make_token(sub=str(uuid.uuid4()), secret="a-different-secret")

    with pytest.raises(InvalidAuthTokenException):
        auth_service.get_current_user_id(token)


def test_missing_exp_claim_raises(auth_service: JwtAuthService) -> None:
    token = make_token(sub=str(uuid.uuid4()), exp_delta=None)

    with pytest.raises(InvalidAuthTokenException):
        auth_service.get_current_user_id(token)


def test_missing_user_id_claim_raises(auth_service: JwtAuthService) -> None:
    token = make_token()

    with pytest.raises(InvalidAuthTokenException):
        auth_service.get_current_user_id(token)


def test_user_id_claim_not_a_uuid_raises(auth_service: JwtAuthService) -> None:
    token = make_token(sub="not-a-uuid")

    with pytest.raises(InvalidAuthTokenException):
        auth_service.get_current_user_id(token)


def test_malformed_token_raises(auth_service: JwtAuthService) -> None:
    with pytest.raises(InvalidAuthTokenException):
        auth_service.get_current_user_id("not-a-jwt-at-all")
