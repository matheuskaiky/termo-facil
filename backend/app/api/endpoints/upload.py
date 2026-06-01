from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db import get_db
from app.services.storage_service import audio_storage, speaker_samples_storage
from app.models import MidiaBruta, JobProcessamentoIA, Modelo, TipoModelo, Depoimento, Inquerito, Usuario
from app.schemas.job import JobResponse
from app.api.deps import RequirePermission, get_current_user
from app.core.permissions import Permission
import uuid
import hashlib
from typing import Optional

_VALID_ROLES = {"Inquiridor", "Depoente"}
_MAGIC_AUDIO = (b'RIFF', b'ID3', b'\xff\xfb', b'\xff\xfa', b'OggS')

router = APIRouter()


def _resolve_modelo(db: Session, tipo: TipoModelo, provided_id: Optional[str]) -> uuid.UUID:
    if provided_id:
        try:
            return uuid.UUID(provided_id)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"ID de modelo inválido: {provided_id}")
    modelo = db.query(Modelo).filter(Modelo.tipo_modelo == tipo).first()
    if not modelo:
        raise HTTPException(status_code=500, detail=f"Nenhum modelo {tipo.value} encontrado no banco de dados.")
    return modelo.id_modelo


@router.post("/audio", response_model=JobResponse, status_code=202)
async def upload_audio(
    id_depoimento: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RequirePermission(Permission.UPLOAD_AUDIO)),
    id_modelo_asr: Optional[str] = Form(None),
    id_modelo_llm: Optional[str] = Form(None),
):
    """
    Receives an audio file, saves it in storage and creates the initial Job in PostgreSQL.
    Model IDs are optional — when omitted the first available model of each type is used.
    """
    if not file.filename.endswith(('.wav', '.mp3', '.m4a', '.opus')):
        raise HTTPException(status_code=400, detail="Formato de áudio não suportado. Use .wav, .mp3, .m4a ou .opus.")

    try:
        uid_depoimento = uuid.UUID(id_depoimento)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de depoimento inválido.")

    depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == uid_depoimento).first()
    if not depoimento:
        raise HTTPException(status_code=404, detail="Depoimento não encontrado.")

    cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
    if cargo_nome == "Escrivão" and depoimento.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Acesso negado: este depoimento pertence a outro escrivão.")
    elif cargo_nome == "Delegado":
        inquerito = db.query(Inquerito).filter(Inquerito.id_inquerito == depoimento.id_inquerito).first()
        if inquerito and inquerito.id_delegacia != current_user.id_delegacia:
            raise HTTPException(status_code=403, detail="Acesso negado: este depoimento pertence a outra delegacia.")

    _MAX_AUDIO_BYTES = 200 * 1024 * 1024
    content = b""
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        content += chunk
        if len(content) > _MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo excede o limite de 200 MB.")

    if len(content) < 12:
        raise HTTPException(status_code=415, detail="Arquivo muito pequeno para ser um áudio válido.")

    magic_bytes = content[:12]
    valid_magic = (
        magic_bytes.startswith(b'RIFF') or
        magic_bytes.startswith(b'ID3') or
        magic_bytes.startswith(b'\xff\xfb') or
        magic_bytes.startswith(b'\xff\xfa') or
        magic_bytes.startswith(b'OggS')
    )
    if not valid_magic:
        raise HTTPException(status_code=415, detail="Formato de arquivo não reconhecido. Envie um arquivo de áudio válido.")

    uid_asr = _resolve_modelo(db, TipoModelo.ASR, id_modelo_asr)
    uid_llm = _resolve_modelo(db, TipoModelo.LLM, id_modelo_llm)

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    storage_path = audio_storage.upload_file(content, unique_filename)

    file_hash = hashlib.sha256(content).hexdigest()

    codec_info = {"filename": file.filename, "content_type": file.content_type}
    stmt = pg_insert(MidiaBruta).values(
        id_depoimento=uid_depoimento,
        hash_sha256=file_hash,
        storage_path=storage_path,
        codec_info=codec_info,
    ).on_conflict_do_update(
        index_elements=["id_depoimento"],
        set_={"hash_sha256": file_hash, "storage_path": storage_path, "codec_info": codec_info},
    )
    db.execute(stmt)

    job_record = JobProcessamentoIA(
        id_depoimento=uid_depoimento,
        id_modelo_asr=uid_asr,
        id_modelo_llm=uid_llm,
    )
    db.add(job_record)
    db.commit()
    db.refresh(job_record)

    from app.core.celery_app import celery_app
    celery_app.send_task("process_audio", args=[str(job_record.id_job)])

    return job_record


@router.post("/speaker-sample", status_code=200)
async def upload_speaker_sample(
    id_depoimento: str = Form(...),
    role: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RequirePermission(Permission.UPLOAD_AUDIO)),
):
    """
    Uploads a short voice sample for a known speaker role (Inquiridor or Depoente).
    The sample is used by the speaker role resolver during audio processing to match
    voices against diarized speakers. Must be called after the main audio upload.
    """
    if role not in _VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"role deve ser um de: {sorted(_VALID_ROLES)}")

    try:
        uid = uuid.UUID(id_depoimento)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de depoimento inválido.")

    midia = db.query(MidiaBruta).filter(MidiaBruta.id_depoimento == uid).first()
    if not midia:
        raise HTTPException(
            status_code=400,
            detail="Faça o upload do áudio principal antes de enviar amostras de voz.",
        )

    cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
    depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == uid).first()
    if depoimento and cargo_nome == "Escrivão" and depoimento.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    content = b""
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        content += chunk
        if len(content) > 10 * 1024 * 1024:  # 10 MB máximo para amostras
            raise HTTPException(status_code=413, detail="Amostra excede 10 MB.")

    if len(content) < 12 or not any(content[:12].startswith(m) for m in _MAGIC_AUDIO):
        raise HTTPException(status_code=415, detail="Formato de áudio não reconhecido.")

    import os
    _, ext = os.path.splitext(file.filename or ".wav")
    storage_key = f"{uid}/{role}{ext or '.wav'}"
    speaker_samples_storage.upload_file(content, storage_key)

    existing_codec = dict(midia.codec_info or {})
    existing_samples = dict(existing_codec.get("speaker_samples", {}))
    existing_samples[role] = storage_key
    existing_codec["speaker_samples"] = existing_samples
    midia.codec_info = existing_codec
    db.commit()

    return {"status": "ok", "role": role, "storage_key": storage_key}
