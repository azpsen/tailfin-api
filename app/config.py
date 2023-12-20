from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    db_uri: str = "localhost"
    db_name: str = "tailfin"

    db_user: str
    db_pwd: str

    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7

    jwt_algorithm: str = "HS256"
    jwt_secret_key: str = "please-change-me"
    jwt_refresh_secret_key: str = "change-me-i-beg-of-you"


@lru_cache
def get_settings():
    return Settings()
