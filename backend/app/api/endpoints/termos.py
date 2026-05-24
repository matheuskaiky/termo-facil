import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any

from app.db import get_db
from app.models import TermosFinais
from app.api.deps import RequirePermission, get_current_user

router = APIRouter()


class SalvarEdicaoRequest(BaseModel):
    txt_editado_humano: str


class TermoDetalheResponse(BaseModel):
    id_depoimento: uuid.UUID
    txt_literal_asr: str | None
    txt_original_ia: str | None
    txt_editado_humano: str | None
    dicionario_ner: Any | None
    segmentos_asr: Any | None

    class Config:
        from_attributes = True


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


@router.get("/{id_depoimento}", response_model=TermoDetalheResponse)
def get_termo(
    id_depoimento: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Retorna o estado atual do termo, incluindo edição humana salva.
    Usado para restaurar o rascunho ao reabrir a tela de auditoria.
    """
    uid = _resolve_uid(id_depoimento)
    return _get_termo_or_404(uid, db)


@router.put("/{id_depoimento}", response_model=TermoDetalheResponse)
def salvar_edicao_humana(
    id_depoimento: str,
    payload: SalvarEdicaoRequest,
    db: Session = Depends(get_db),
    _=Depends(RequirePermission("EDITAR_TERMO")),
):
    """
    Persiste o texto revisado pelo escrivão (txt_editado_humano).
    O PDF gerado subsequentemente usará este texto no lugar do original da IA.
    """
    uid = _resolve_uid(id_depoimento)
    termo = _get_termo_or_404(uid, db)
    termo.txt_editado_humano = payload.txt_editado_humano
    db.commit()
    db.refresh(termo)
    return termo
