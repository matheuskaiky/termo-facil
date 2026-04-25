from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema Inteligente de Redação de Termos de Depoimentos - SSP-PI",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configuração de CORS (Cross-Origin Resource Sharing)
# No ambiente de produção, origens devem ser restritas à rede da SSP-PI
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
    Endpoint para verificação de saúde da API.
    """
    return {"status": "ok", "system": settings.PROJECT_NAME}

# Futuramente, as rotas da aplicação serão incluídas aqui:
# app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
