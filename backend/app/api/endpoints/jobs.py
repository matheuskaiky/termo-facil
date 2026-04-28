from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import JobProcessamentoIA, TermosFinais
from app.schemas.job import JobResponse, JobResultResponse
import uuid

router = APIRouter()

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Returns the current status of a processing Job in the queue.
    """
    job = db.query(JobProcessamentoIA).filter(JobProcessamentoIA.id_job == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return job

@router.get("/{job_id}/resultado", response_model=JobResultResponse)
def get_job_result(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Returns the result of a Job processing
    """

    termos_finais = db.query(TermosFinais).filter(TermosFinais.id_job == job_id).first()

    if not termos_finais:
        raise HTTPException(status_code=404, detail="No transcription was found for this Job")
    
    return termos_finais