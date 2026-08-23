from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    JWT_SECRET: str | None = None
    JWT_ALGORITHM: str
    JWT_USER_ID_CLAIM: str
