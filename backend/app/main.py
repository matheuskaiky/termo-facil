import sys
import os
# Hack to allow running main.py directly from the IDE ("Run" button) from the root folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import SECRET_KEY

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema Inteligente de Redação de Termos de Depoimentos - SSP-PI",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)


@app.on_event("startup")
async def startup_event():
    """Validate production security requirements on startup."""
    if settings.APP_ENV == "production":
        if SECRET_KEY == "dev-secret-inseguro-troque-em-producao":
            raise RuntimeError(
                "❌ ERRO CRÍTICO: JWT_SECRET_KEY usa valor padrão inseguro em produção!\n"
                "Configure JWT_SECRET_KEY no arquivo .env com uma chave segura (>32 caracteres aleatórios)."
            )

# CORS Configuration (Cross-Origin Resource Sharing)
# In production, origins should be restricted to the SSP-PI network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
async def health_check():
    """
    Endpoint for API health check.
    """
    return {"status": "ok", "system": settings.PROJECT_NAME}

from app.api.api import api_router

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
