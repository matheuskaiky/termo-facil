from fastapi import APIRouter
from app.api.endpoints import upload, jobs

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload", tags=["Upload e Ingestão"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Fila de Jobs"])
