import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve the .env path relative to the backend/ root directory, not the CWD
_BACKEND_DIR = Path(__file__).resolve().parent.parent  # app/core/config.py -> app/ -> backend/
_ENV_FILE = _BACKEND_DIR / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Termo Fácil"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    
    # Database Configurations
    POSTGRES_USER: str = "termo_user"
    POSTGRES_PASSWORD: str = "termo_password"
    POSTGRES_SERVER: str = "127.0.0.1"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "termo_facil"
    
    # Redis / Celery Configurations
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    
    # MinIO
    MINIO_ENDPOINT: str = "127.0.0.1:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "adminpassword"
    MINIO_SECURE: bool = False
    
    @property
    def sync_database_uri(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def async_database_uri(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    class Config:
        case_sensitive = True
        env_file = str(_ENV_FILE)

settings = Settings()
