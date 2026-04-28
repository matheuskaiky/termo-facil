from fastapi import APIRouter
from app.api.endpoints import upload, jobs

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload", tags=["Upload & Ingestion"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs Queue"])
