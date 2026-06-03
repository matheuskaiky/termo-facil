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
from app.utils.lock import assert_not_signed

router = APIRouter()


class SalvarEdicaoRequest(BaseModel):
    txt_editado_humano: str


class TermoResumoResponse(BaseModel):
    """Minimized response for list endpoints — omits raw NER/ASR data per LGPD Art. 46."""
    model_config = ConfigDict(from_attributes=True)

    id_depoimento: uuid.UUID
    txt_original_ia: str | None
    txt_editado_humano: str | None


class SpeakerInfo(BaseModel):
    role: str
    nome: str | None = None


class SetSpeakersRequest(BaseModel):
    # { "<label atual nos segmentos>": {"role": "Depoente|Inquiridor", "nome": "opcional"} }
    mapping: dict[str, SpeakerInfo]


class TermoDetalheResponse(BaseModel):
    """Full response for the audit screen — includes NER/ASR for in-session use only."""
    model_config = ConfigDict(from_attributes=True)

    id_depoimento: uuid.UUID
    txt_literal_asr: str | None
    txt_original_ia: str | None
    txt_editado_humano: str | None
    dicionario_ner: Any | None
    segmentos_asr: Any | None
    ner_entidades: Any | None = None
    confianca_asr: float | None = None
    confianca_ner: float | None = None
    tempo_asr_ms: float | None = None
    tempo_ner_ms: float | None = None
    tempo_llm_ms: float | None = None
    tempo_total_ms: float | None = None
    nome_depoente: str | None = None
    num_procedimento: str | None = None
    assinado: bool = False


def _detalhe(termo: TermosFinais) -> dict:
    dep = termo.depoimento
    return {
        "id_depoimento": termo.id_depoimento,
        "txt_literal_asr": termo.txt_literal_asr,
        "txt_original_ia": termo.txt_original_ia,
        "txt_editado_humano": termo.txt_editado_humano,
        "dicionario_ner": termo.dicionario_ner,
        "segmentos_asr": termo.segmentos_asr,
        "ner_entidades": termo.ner_entidades,
        "confianca_asr": termo.confianca_asr,
        "confianca_ner": termo.confianca_ner,
        "tempo_asr_ms": termo.tempo_asr_ms,
        "tempo_ner_ms": termo.tempo_ner_ms,
        "tempo_llm_ms": termo.tempo_llm_ms,
        "tempo_total_ms": termo.tempo_total_ms,
        "nome_depoente": dep.depoente.nome_depoente if dep and dep.depoente else None,
        "num_procedimento": dep.inquerito.num_procedimento if dep and dep.inquerito else None,
        "assinado": termo.hash_pdf is not None,
    }


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
    return _detalhe(termo)


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
    assert_not_signed(db, uid)

    cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
    if cargo_nome == "Escrivão" and termo.depoimento.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Acesso negado: este termo pertence a outro escrivão.")

    termo.txt_editado_humano = payload.txt_editado_humano
    db.commit()
    db.refresh(termo)
    return _detalhe(termo)


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
    assert_not_signed(db, uid)

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

    return _detalhe(termo)


@router.post("/{id_depoimento}/speakers", response_model=TermoDetalheResponse)
def set_speakers(
    id_depoimento: str,
    payload: SetSpeakersRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RequirePermission(Permission.EDITAR_TERMO)),
):
    """
    Manual speaker labelling: the reviewer listened to a sample of each detected
    speaker and assigns the role (Depoente/Inquiridor) and an optional name.
    Rewrites segmentos_asr[].speaker (and .speaker_nome). Blocked once signed.
    """
    uid = _resolve_uid(id_depoimento)
    termo = _get_termo_or_404(uid, db)
    assert_not_signed(db, uid)

    cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
    if cargo_nome == "Escrivão" and termo.depoimento.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Acesso negado: este termo pertence a outro escrivão.")

    segments = list(termo.segmentos_asr or [])
    if not segments:
        raise HTTPException(status_code=400, detail="Nenhum segmento disponível.")

    mapping = payload.mapping
    new_segments = []
    for s in segments:
        info = mapping.get(s.get("speaker"))
        if info:
            s = {**s, "speaker": info.role, "speaker_nome": info.nome}
        new_segments.append(s)
    termo.segmentos_asr = new_segments
    db.commit()
    db.refresh(termo)
    log_access("POST /termos/{id}/speakers", str(uid), db, current_user)
    return _detalhe(termo)
