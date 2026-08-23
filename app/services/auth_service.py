import logging
from uuid import UUID

import jwt

from app.cofigurations.auth_settings import AuthSettings
from app.exceptions.domain_exceptions import InvalidAuthTokenException
from app.services.abstractions.interfaces import AbstractAuthService


class JwtAuthService(AbstractAuthService):
    def __init__(self, settings: AuthSettings):
        self._settings = settings
        self._logger = logging.getLogger(__name__)

    def get_current_user_id(self, token: str) -> UUID:
        try:
            payload = jwt.decode(
                token,
                self._settings.JWT_SECRET,
                algorithms=[self._settings.JWT_ALGORITHM],
                options={"require": ["exp", self._settings.JWT_USER_ID_CLAIM]},
            )
        except jwt.PyJWTError as e:
            self._logger.warning(
                "JWT validation failed",
                extra={"event": "jwt_invalid", "error": str(e)},
            )
            raise InvalidAuthTokenException(str(e))

        raw_user_id = payload.get(self._settings.JWT_USER_ID_CLAIM)
        try:
            return UUID(str(raw_user_id))
        except (ValueError, TypeError):
            self._logger.warning(
                "JWT user id claim is not a valid UUID",
                extra={"event": "jwt_invalid_user_id", "claim": self._settings.JWT_USER_ID_CLAIM},
            )
            raise InvalidAuthTokenException(f"claim '{self._settings.JWT_USER_ID_CLAIM}' is not a valid UUID")
