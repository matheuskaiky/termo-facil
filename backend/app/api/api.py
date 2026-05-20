from fastapi import APIRouter
from app.api.endpoints import upload, jobs, admin, auth, pdf

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload", tags=["Upload & Ingestion"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs Queue"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & RBAC"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth Simulator"])
api_router.include_router(pdf.router, prefix="/pdf", tags=["PDF Generation"])
