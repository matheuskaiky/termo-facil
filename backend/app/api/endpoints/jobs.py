from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import JobProcessamentoIA
from app.schemas.job import JobResponse
import uuid

router = APIRouter()

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retorna o status atual de um Job de processamento na fila.
    """
    job = db.query(JobProcessamentoIA).filter(JobProcessamentoIA.id_job == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
        
    return job
