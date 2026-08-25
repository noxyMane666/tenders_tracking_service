from pydantic_settings import BaseSettings


class AppLimitsSettings(BaseSettings):
    REQUEST_BODY_MAX_SIZE: int