from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.storage_service import audio_storage
from app.models import MidiaBruta, JobProcessamentoIA
from app.schemas.job import JobResponse
from app.api.deps import RequirePermission
import uuid
import hashlib

router = APIRouter()

@router.post("/audio", response_model=JobResponse, status_code=202)
async def upload_audio(
    id_depoimento: str = Form(...),
    id_modelo_asr: str = Form(...),
    id_modelo_llm: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(RequirePermission('UPLOAD_AUDIO'))
):
    """
    Receives an audio file, saves it in storage and creates the initial Job in PostgreSQL.
    """
    # 1. Basic extension validation
    if not file.filename.endswith(('.wav', '.mp3', '.m4a')):
        raise HTTPException(status_code=400, detail="Unsupported audio format.")
        
    content = await file.read()
    
    # 2. Upload to storage
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    storage_path = audio_storage.upload_file(content, unique_filename)
    
    # File hash for integrity (SHA256)
    file_hash = hashlib.sha256(content).hexdigest()
    
    # 3. Save or update raw media record to Database
    media_record = db.query(MidiaBruta).filter(MidiaBruta.id_depoimento == id_depoimento).first()
    if media_record:
        media_record.hash_sha256 = file_hash
        media_record.storage_path = storage_path
        media_record.codec_info = {"filename": file.filename, "content_type": file.content_type}
    else:
        media_record = MidiaBruta(
            id_depoimento=id_depoimento,
            hash_sha256=file_hash,
            storage_path=storage_path,
            codec_info={"filename": file.filename, "content_type": file.content_type}
        )
        db.add(media_record)
    
    # 4. Create the Job record
    job_record = JobProcessamentoIA(
        id_depoimento=id_depoimento,
        id_modelo_asr=id_modelo_asr,
        id_modelo_llm=id_modelo_llm
        # Status defaults to PENDENTE
    )
    db.add(job_record)
    db.commit()
    db.refresh(job_record)
    
    # Trigger the background Celery task
    from app.core.celery_app import celery_app
    celery_app.send_task("process_audio", args=[str(job_record.id_job)])
    
    return job_record
