from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.minio_service import minio_service
from app.models import MidiaBruta, JobProcessamentoIA
from app.schemas.job import JobResponse
import uuid
import hashlib

router = APIRouter()

@router.post("/audio", response_model=JobResponse, status_code=202)
async def upload_audio(
    id_depoimento: str = Form(...),
    id_modelo_asr: str = Form(...),
    id_modelo_llm: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Recebe um arquivo de áudio, salva no MinIO e cria o Job inicial no PostgreSQL.
    """
    # 1. Validação simples de extensão
    if not file.filename.endswith(('.wav', '.mp3', '.m4a')):
        raise HTTPException(status_code=400, detail="Formato de áudio não suportado.")
        
    content = await file.read()
    
    # 2. Upload para o MinIO
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    storage_path = minio_service.upload_file(content, unique_filename)
    
    # Hash do arquivo para integridade (SHA256)
    file_hash = hashlib.sha256(content).hexdigest()
    
    # 3. Salvar Midia Bruta no Banco
    midia = MidiaBruta(
        id_depoimento=id_depoimento,
        hash_sha256=file_hash,
        storage_path=storage_path,
        codec_info={"filename": file.filename, "content_type": file.content_type}
    )
    db.add(midia)
    
    # 4. Criar o Job
    job = JobProcessamentoIA(
        id_depoimento=id_depoimento,
        id_modelo_asr=id_modelo_asr,
        id_modelo_llm=id_modelo_llm
        # O status entra como PENDENTE por padrão
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Aciona a task do Celery em segundo plano
    from app.core.celery_app import celery_app
    celery_app.send_task("processar_audio", args=[str(job.id_job)])
    
    return job
