from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False)

    app_name: str = 'Secure Auth System'
    environment: str = 'development'
    debug: bool = False
    api_v1_prefix: str = '/api/v1'

    access_token_secret_key: str = Field('change-me-access-secret-in-production', min_length=16)
    refresh_token_secret_key: str = Field('change-me-refresh-secret-in-production', min_length=16)
    password_reset_secret_key: str = Field('change-me-reset-secret-in-production', min_length=16)
    algorithm: str = 'HS256'
    token_issuer: str = 'secure-auth-system'
    token_audience: str = 'secure-auth-api'
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    password_reset_expire_minutes: int = 20

    database_url: str = 'sqlite:///./secure_auth.db'
    redis_url: str = 'redis://redis:6379/0'
    allowed_origins: list[str] = ['http://localhost:3000', 'http://localhost:5173']

    login_rate_limit_max_attempts: int = 5
    login_rate_limit_window_seconds: int = 300

    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
