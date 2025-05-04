import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Math Concepts API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    TESTING: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production").lower()  # production, development, or testing
    PASSWORD_SALT: str = os.getenv("PASSWORD_SALT", "dev_password_salt")
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key")  # A fallback value for local testing
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Database
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "app_db")
    DBTESTLINK: str | None = os.getenv("DBTESTLINK")  # Optional during testing

    @property
    def DATABASE_URL(self) -> str:
        if self.ENVIRONMENT == "testing":
            print("Test Environment")
            return self.DBTESTLINK or "sqlite:///./test.db"  # Defaults to SQLite for testing if DBTESTLINK is not provided
        else:
            print(f"{'Development' if self.ENVIRONMENT == 'development' else 'Production'} Environment")
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]  # Modify this for stricter security in production
    model_config = ConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()

    # Environment-specific overrides
    if settings.ENVIRONMENT == "testing":
        settings.DEBUG = True
        settings.TESTING = True
    elif settings.ENVIRONMENT == "development":
        settings.DEBUG = True
        settings.TESTING = False
    else:  # production
        settings.DEBUG = False
        settings.TESTING = False

    return settings


settings = get_settings()
