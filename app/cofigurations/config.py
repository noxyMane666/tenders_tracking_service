import os

from dotenv import load_dotenv

from app.cofigurations.app_limits_settings import AppLimitsSettings
from app.cofigurations.auth_settings import AuthSettings
from app.cofigurations.cache_settings import CacheSettings
from app.cofigurations.db_settings import DataBaseSettings

load_dotenv()

class Configuration:
    def __init__(self):
        self.db_settings = self._load_db_settings()
        self.auth_settings = self._load_auth_settings()
        self.app_limits_settings = self._load_app_limits()
        self.cache_settings = self._load_cache_settings()

        self._validate_required_fields()


    @staticmethod
    def _load_db_settings() -> DataBaseSettings:
        return DataBaseSettings(
            DB_CONNECTION_STRING=os.getenv("DB_CONNECTION_STRING"),
            ECHO=os.getenv("DB_ECHO", "false").lower() == "true",
            MAX_POOL_SIZE=int(os.getenv("MAX_POOL_SIZE", "10")),
            MAX_OVERFLOW=int(os.getenv("MAX_OVERFLOW", "20")),
            POOL_TIMEOUT=int(os.getenv("POOL_TIMEOUT", "30"))
        )

    @staticmethod
    def _load_auth_settings() -> AuthSettings:
        return AuthSettings(
            JWT_SECRET=os.getenv("JWT_SECRET"),
            JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
            JWT_USER_ID_CLAIM=os.getenv("JWT_USER_ID_CLAIM", "sub"),
        )

    @staticmethod
    def _load_app_limits() -> AppLimitsSettings:
        return AppLimitsSettings(
            REQUEST_BODY_MAX_SIZE=int(os.getenv("REQUEST_BODY_MAX_SIZE", "32768"))
        )

    @staticmethod
    def _load_cache_settings() -> CacheSettings:
        return CacheSettings(
            REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            CACHE_TTL_SECONDS=int(os.getenv("CACHE_TTL_SECONDS", "60"))
        )

    def _validate_required_fields(self):
        required_fields = {
            "DB_CONNECTION_STRING": self.db_settings.DB_CONNECTION_STRING,
            "JWT_SECRET": self.auth_settings.JWT_SECRET,
            "REQUEST_BODY_MAX_SIZE": self.app_limits_settings.REQUEST_BODY_MAX_SIZE
        }

        for field_name, value in required_fields.items():
            if not value:
                raise RuntimeError(f"Missing settings param: {field_name}")
