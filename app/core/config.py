from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    password_reset_token_expire_minutes: int = Field(30, env="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES")
    frontend_url: str = Field("http://localhost:3000", env="FRONTEND_URL")
    geniuspay_api_key: str = Field(..., env="GENIUSPAY_API_KEY")
    geniuspay_api_secret: str = Field(..., env="GENIUSPAY_API_SECRET")
    geniuspay_webhook_secret: str = Field(..., env="GENIUSPAY_WEBHOOK_SECRET")
    geniuspay_environment: str = Field("sandbox", env="GENIUSPAY_ENVIRONMENT")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    deepl_api_key: str | None = Field(None, env="DEEPL_API_KEY")
    allowed_origins: str = Field("http://localhost:3000,http://localhost:5173", env="ALLOWED_ORIGINS")
    smtp_host: str | None = Field(None, env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_user: str | None = Field(None, env="SMTP_USER")
    smtp_password: str | None = Field(None, env="SMTP_PASSWORD")
    smtp_from: str | None = Field(None, env="SMTP_FROM")
    smtp_starttls: bool = Field(True, env="SMTP_STARTTLS")
    smtp_use_ssl: bool = Field(False, env="SMTP_USE_SSL")

    class Config:
        # Le dernier fichier l'emporte : .env doit venir après .env.example.
        env_file = [".env.example", ".env"]
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
