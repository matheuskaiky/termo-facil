import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from typing import Any

from app.db import get_db
from app.models import TermosFinais, Depoimento, Inquerito, Usuario
from app.api.deps import RequirePermission, get_current_user

router = APIRouter()


class SalvarEdicaoRequest(BaseModel):
    txt_editado_humano: str


class TermoDetalheResponse(BaseModel):
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
    cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""

    query = db.query(TermosFinais).join(
        Depoimento, TermosFinais.id_depoimento == Depoimento.id_depoimento
    )

    if cargo_nome == "Escrivão":
        query = query.filter(Depoimento.id_usuario == current_user.id_usuario)
    elif cargo_nome == "Delegado":
        query = query.join(Inquerito, Depoimento.id_inquerito == Inquerito.id_inquerito)
        query = query.filter(Inquerito.id_delegacia == current_user.id_delegacia)
    # Admin / Gestor Estratégico: sem filtro

    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return {"total": total, "items": [TermoDetalheResponse.model_validate(t) for t in items]}


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

    return termo


@router.put("/{id_depoimento}", response_model=TermoDetalheResponse)
def salvar_edicao_humana(
    id_depoimento: str,
    payload: SalvarEdicaoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RequirePermission("EDITAR_TERMO")),
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
