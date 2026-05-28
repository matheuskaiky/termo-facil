import logging
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from typing import Any

logger = logging.getLogger(__name__)

from app.db import get_db
from app.models import TermosFinais, Depoimento, Inquerito, Usuario
from app.api.deps import RequirePermission, get_current_user
from app.core.permissions import Permission
from app.utils.audit import log_access
from app.utils.query_scopes import apply_depoimento_scope

router = APIRouter()


class SalvarEdicaoRequest(BaseModel):
    txt_editado_humano: str


class TermoResumoResponse(BaseModel):
    """Minimized response for list endpoints — omits raw NER/ASR data per LGPD Art. 46."""
    model_config = ConfigDict(from_attributes=True)

    id_depoimento: uuid.UUID
    txt_original_ia: str | None
    txt_editado_humano: str | None


class TermoDetalheResponse(BaseModel):
    """Full response for the audit screen — includes NER/ASR for in-session use only."""
    model_config = ConfigDict(from_attributes=True)

    id_depoimento: uuid.UUID
    txt_literal_asr: str | None
    txt_original_ia: str | None
    txt_editado_humano: str | None
    dicionario_ner: Any | None
    segmentos_asr: Any | None


def _resolve_uid(id_depoimento: str) -> uuid.UUID:
    try:
        return uuid.UUID(id_depoimento)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de depoimento inválido.")


def _get_termo_or_404(uid: uuid.UUID, db: Session) -> TermosFinais:
    termo = db.query(TermosFinais).filter(TermosFinais.id_depoimento == uid).first()
    if not termo:
        raise HTTPException(status_code=404, detail="Termo não encontrado para este depoimento.")
    return termo


@router.get("/")
def list_termos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
):
    query = db.query(TermosFinais).join(
        Depoimento, TermosFinais.id_depoimento == Depoimento.id_depoimento
    )
    query = apply_depoimento_scope(query, current_user)

    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return {"total": total, "items": [TermoResumoResponse.model_validate(t) for t in items]}


@router.get("/{id_depoimento}", response_model=TermoDetalheResponse)
def get_termo(
    id_depoimento: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna o estado atual do termo, incluindo edição humana salva.
    Usado para restaurar o rascunho ao reabrir a tela de auditoria.
    """
    uid = _resolve_uid(id_depoimento)
    termo = _get_termo_or_404(uid, db)

    cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
    if cargo_nome == "Escrivão" and termo.depoimento.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Acesso negado: este termo pertence a outro escrivão.")
    elif cargo_nome == "Delegado":
        inquerito = db.query(Inquerito).filter(Inquerito.id_inquerito == termo.depoimento.id_inquerito).first()
        if inquerito and inquerito.id_delegacia != current_user.id_delegacia:
            raise HTTPException(status_code=403, detail="Acesso negado: este termo pertence a outra delegacia.")

    log_access("GET /termos/{id}", str(uid), db, current_user)
    return termo


@router.put("/{id_depoimento}", response_model=TermoDetalheResponse)
def salvar_edicao_humana(
    id_depoimento: str,
    payload: SalvarEdicaoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RequirePermission(Permission.EDITAR_TERMO)),
):
    """
    Persiste o texto revisado pelo escrivão (txt_editado_humano).
    O PDF gerado subsequentemente usará este texto no lugar do original da IA.
    """
    uid = _resolve_uid(id_depoimento)
    termo = _get_termo_or_404(uid, db)

    cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
    if cargo_nome == "Escrivão" and termo.depoimento.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Acesso negado: este termo pertence a outro escrivão.")

    termo.txt_editado_humano = payload.txt_editado_humano
    db.commit()
    db.refresh(termo)
    return termo


@router.post("/{id_depoimento}/reclassify-speakers", response_model=TermoDetalheResponse)
async def reclassify_speakers(
    id_depoimento: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RequirePermission(Permission.EDITAR_TERMO)),
    file: UploadFile | None = File(None),
):
    """
    Re-runs speaker role identification on the already-transcribed segments without
    re-executing ASR, NER, or LLM. Two modes:
    - With audio file: audio-based embedding match (voice sample of a known speaker)
    - Without file: text-based pattern analysis
    Updates TermosFinais.segmentos_asr in place.
    """
    import os
    import tempfile
    from app.services.speaker_role_service import (
        AudioBasedRoleResolver, SpeakerRoleResolver, TextBasedRoleResolver,
    )

    uid = _resolve_uid(id_depoimento)
    termo = _get_termo_or_404(uid, db)

    cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
    if cargo_nome == "Escrivão" and termo.depoimento.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Acesso negado: este termo pertence a outro escrivão.")

    segments = list(termo.segmentos_asr or [])
    if not segments:
        raise HTTPException(status_code=400, detail="Nenhum segmento disponível para reclassificação.")

    resolver = SpeakerRoleResolver(
        text_resolver=TextBasedRoleResolver(),
        audio_resolver=AudioBasedRoleResolver(),
    )

    tmp_path: str | None = None
    try:
        known_samples: dict[str, str] | None = None
        if file and file.filename:
            content = await file.read()
            suffix = os.path.splitext(file.filename)[1] or ".wav"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            known_samples = {"Inquiridor": tmp_path}

        role_mapping = resolver.resolve(segments, known_samples=known_samples)

        if role_mapping:
            segments = [
                {**s, "speaker": role_mapping.get(s["speaker"], s["speaker"])}
                for s in segments
            ]
            termo.segmentos_asr = segments
            db.commit()
            db.refresh(termo)
            logger.info("reclassify_speakers: mapping=%s depoimento=%s", role_mapping, uid)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return termo
