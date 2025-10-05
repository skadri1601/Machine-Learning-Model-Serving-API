from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ML Model Serving API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/mlapi"

    # Model Storage
    MODEL_STORAGE_PATH: str = "./models"
    MAX_MODEL_SIZE_MB: int = 500

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Monitoring
    ENABLE_METRICS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
