import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import MidiaBruta, Depoimento, Inquerito, Usuario
from app.services.storage_service import audio_storage
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/{id_depoimento}")
def get_audio_url(
    id_depoimento: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
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

    depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == uid).first()
    if depoimento:
        cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
        if cargo_nome == "Escrivão" and depoimento.id_usuario != current_user.id_usuario:
            raise HTTPException(status_code=403, detail="Acesso negado: este áudio pertence a outro escrivão.")
        elif cargo_nome == "Delegado":
            inquerito = db.query(Inquerito).filter(Inquerito.id_inquerito == depoimento.id_inquerito).first()
            if inquerito and inquerito.id_delegacia != current_user.id_delegacia:
                raise HTTPException(status_code=403, detail="Acesso negado: este áudio pertence a outra delegacia.")

    try:
        url = audio_storage.generate_presigned_url(midia.storage_path, expiration=3600)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar URL de acesso ao áudio: {str(e)}")

    return {"audio_url": url}
