from pydantic_settings import BaseSettings


class DataBaseSettings(BaseSettings):
    DB_CONNECTION_STRING: str | None = None
    ECHO: bool
    MAX_POOL_SIZE: int
    MAX_OVERFLOW: int
    POOL_TIMEOUT: int