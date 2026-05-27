from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import JobProcessamentoIA, TermosFinais, Depoimento, Inquerito, Usuario
from app.schemas.job import JobResponse, JobResultResponse
from app.api.deps import RequirePermission, get_current_user
import uuid

router = APIRouter(dependencies=[Depends(RequirePermission('EDITAR_TERMO'))])

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """
    Returns the current status of a processing Job in the queue.
    """
    job = db.query(JobProcessamentoIA).filter(JobProcessamentoIA.id_job == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == job.id_depoimento).first()
    if depoimento:
        cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
        if cargo_nome == "Escrivão" and depoimento.id_usuario != current_user.id_usuario:
            raise HTTPException(status_code=403, detail="Acesso negado: este job pertence a outro escrivão.")
        elif cargo_nome == "Delegado":
            inquerito = db.query(Inquerito).filter(Inquerito.id_inquerito == depoimento.id_inquerito).first()
            if inquerito and inquerito.id_delegacia != current_user.id_delegacia:
                raise HTTPException(status_code=403, detail="Acesso negado: este job pertence a outra delegacia.")

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