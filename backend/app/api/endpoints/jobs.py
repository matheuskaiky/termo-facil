from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import JobProcessamentoIA, TermosFinais, Depoimento, Inquerito, Usuario, StatusJob
from app.schemas.job import JobResponse, JobResultResponse
from app.api.deps import RequirePermission, get_current_user
from app.core.permissions import Permission
from app.utils.audit import log_access
from app.utils.lock import assert_not_signed
import uuid

router = APIRouter(dependencies=[Depends(RequirePermission(Permission.EDITAR_TERMO))])

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

    log_access("GET /jobs/{id}", str(job_id), db, current_user)
    return job


@router.post("/{job_id}/reprocessar", response_model=JobResponse)
def reprocessar_job(job_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """
    Re-runs the AI pipeline on the SAME audio. Only allowed when the job is in
    ERRO state — it's a recovery action, not a normal re-run. Blocked once signed.
    Resets the job to Pendente (the task moves it to Transcrevendo) and re-dispatches.
    """
    job = db.query(JobProcessamentoIA).filter(JobProcessamentoIA.id_job == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    assert_not_signed(db, job.id_depoimento)

    if job.status != StatusJob.ERRO:
        raise HTTPException(
            status_code=409,
            detail="Reprocessamento só é permitido para jobs que falharam (status Erro).",
        )
    if not (job.depoimento and job.depoimento.midia_bruta):
        raise HTTPException(status_code=400, detail="Áudio do processo não encontrado para reprocessar.")

    params = dict(job.parametros_ia or {})
    params.pop("erro", None)
    job.parametros_ia = params
    job.status = StatusJob.PENDENTE
    db.commit()
    db.refresh(job)

    from app.core.celery_app import celery_app
    celery_app.send_task("process_audio", args=[str(job.id_job)])

    log_access("POST /jobs/{id}/reprocessar", str(job_id), db, current_user)
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