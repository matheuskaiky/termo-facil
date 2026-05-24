import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import MidiaBruta
from app.services.storage_service import audio_storage
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/{id_depoimento}")
def get_audio_url(
    id_depoimento: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Returns a presigned URL for the raw audio file of a testimony.
    Used by the frontend audio player to stream the recording.
    """
    try:
        uid = uuid.UUID(id_depoimento)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de depoimento inválido.")

    midia = db.query(MidiaBruta).filter(MidiaBruta.id_depoimento == uid).first()
    if not midia:
        raise HTTPException(status_code=404, detail="Mídia de áudio não encontrada para este depoimento.")

    try:
        url = audio_storage.generate_presigned_url(midia.storage_path, expiration=3600)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar URL de acesso ao áudio: {str(e)}")

    return {"audio_url": url}
