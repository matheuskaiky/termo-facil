from fastapi import APIRouter
from app.api.endpoints import upload, jobs, admin, auth, pdf, processos, termos, audio, metricas, debug

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload", tags=["Upload & Ingestion"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs Queue"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & RBAC"])
api_router.include_router(admin.reset_router, prefix="/admin", tags=["Admin & RBAC"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(pdf.router, prefix="/pdf", tags=["PDF Generation"])
api_router.include_router(processos.router, prefix="/processos", tags=["Processos"])
api_router.include_router(termos.router, prefix="/termos", tags=["Termos & Edição Humana"])
api_router.include_router(audio.router, prefix="/audio", tags=["Áudio & Mídia"])
api_router.include_router(metricas.router, prefix="/metricas", tags=["Métricas & ROI"])
api_router.include_router(debug.router, prefix="/debug", tags=["Dev/Debug"])
api_router.include_router(debug.models_router, prefix="/models", tags=["Dev/Debug"])
