from pydantic_settings import BaseSettings


class CacheSettings(BaseSettings):
    REDIS_URL: str
    CACHE_TTL_SECONDS: int
