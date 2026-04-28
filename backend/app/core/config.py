from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Termo Fácil"
    API_V1_STR: str = "/api/v1"
    
    # Database Configurations
    POSTGRES_USER: str = "termo_user"
    POSTGRES_PASSWORD: str = "termo_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "termo_facil"
    
    # Redis / Celery Configurations
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "adminpassword"
    MINIO_SECURE: bool = False
    
    @property
    def sync_database_uri(self) -> str:
        return f"postgresql+pg8000://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def async_database_uri(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
