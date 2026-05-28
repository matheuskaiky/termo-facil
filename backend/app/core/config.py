from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env path relative to the backend/ root directory, not the CWD
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # app/core/config.py -> app/core/ -> app/ -> backend/
_ENV_FILE = _BACKEND_DIR / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Termo Fácil"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    ALLOWED_ORIGINS: list = ["http://localhost:4200"]

    # Database Configurations
    POSTGRES_USER: str = "termo_user"
    POSTGRES_PASSWORD: str  # ← NO DEFAULT — must be set via .env or env var
    POSTGRES_SERVER: str = "127.0.0.1"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "termo_facil"

    # Redis / Celery Configurations
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # MinIO (secrets must be provided via .env — no defaults)
    MINIO_ENDPOINT: str = "127.0.0.1:9000"
    MINIO_ACCESS_KEY: str  # ← NO DEFAULT
    MINIO_SECRET_KEY: str  # ← NO DEFAULT
    MINIO_SECURE: bool = False

    # JWT Security (must be provided via .env — no defaults)
    JWT_SECRET_KEY: str  # ← NO DEFAULT

    # AI Pipeline providers
    # LLM_PROVIDER: "ollama" (dev, single-GPU) | "vllm" (prod, PagedAttention)
    LLM_PROVIDER: str = "ollama"
    # DIARIZATION_PROVIDER: "heuristic" (gap-based, no GPU) | "pyannote" (real diarization, HPC)
    DIARIZATION_PROVIDER: str = "heuristic"
    PYANNOTE_HF_TOKEN: str | None = None  # required when DIARIZATION_PROVIDER=pyannote
    
    @property
    def sync_database_uri(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def async_database_uri(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    model_config = SettingsConfigDict(case_sensitive=True, env_file=str(_ENV_FILE))

settings = Settings()
