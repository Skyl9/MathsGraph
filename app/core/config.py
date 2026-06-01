import logging
from functools import lru_cache

# load_dotenv() n'est plus nécessaire car pydantic_settings lit le .env nativement !
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Math Concepts API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    TESTING: bool = False

    ENVIRONMENT: str = "production"
    PASSWORD_SALT: str = "dev_password_salt"

    # Authentication
    SECRET_KEY: str = Field(..., description="Clé secrète obligatoire pour JWT")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "app_db"
    DB_URL_ENV: str | None = Field(default=None, validation_alias="DATABASE_URL")
    DBTESTLINK: str | None = None
    REDIS_URL: str = "redis://localhost:6379"

    # E-mail
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Frontend URL (utilisé pour les liens dans les emails)
    FRONTEND_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def lowercase_environment(cls, v: str) -> str:
        return v.lower() if isinstance(v, str) else v

    @property
    def DATABASE_URL(self) -> str:
        if self.ENVIRONMENT == "testing":
            return self.DBTESTLINK or "sqlite:///./test.db"

        if self.DB_URL_ENV:
            return self.DB_URL_ENV

        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()  # type: ignore

    # Environment-specific overrides
    if settings.ENVIRONMENT == "testing":
        settings.DEBUG = True
        settings.TESTING = True
    elif settings.ENVIRONMENT == "development":
        settings.DEBUG = True
        settings.TESTING = False
        if settings.BACKEND_CORS_ORIGINS == ["*"]:
            settings.BACKEND_CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8080", "http://localhost:8000"]
        if settings.FRONTEND_URL == "http://localhost:8000":
            settings.FRONTEND_URL = "http://localhost:8000"
    else:  # production
        if settings.BACKEND_CORS_ORIGINS == ["*"]:
            settings.BACKEND_CORS_ORIGINS = ["https://mathsgraphfrontend-production.up.railway.app"]
        if settings.FRONTEND_URL == "http://localhost:8000":
            settings.FRONTEND_URL = "https://mathsgraphfrontend-production.up.railway.app"
        settings.DEBUG = False
        settings.TESTING = False

    return settings


settings = get_settings()
