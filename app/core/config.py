from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    geniuspay_api_key: str = Field(..., env="GENIUSPAY_API_KEY")
    geniuspay_api_secret: str = Field(..., env="GENIUSPAY_API_SECRET")
    geniuspay_webhook_secret: str = Field(..., env="GENIUSPAY_WEBHOOK_SECRET")
    geniuspay_environment: str = Field("sandbox", env="GENIUSPAY_ENVIRONMENT")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")

    class Config:
        env_file = [".env", ".env.example"]
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
