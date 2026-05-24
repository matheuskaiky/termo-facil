import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TermosFinais
from app.api.deps import RequirePermission

router = APIRouter()


class SalvarEdicaoRequest(BaseModel):
    txt_editado_humano: str


class TermoResponse(BaseModel):
    id_depoimento: uuid.UUID
    txt_editado_humano: str | None

    class Config:
        from_attributes = True


@router.put("/{id_depoimento}", response_model=TermoResponse)
def salvar_edicao_humana(
    id_depoimento: str,
    payload: SalvarEdicaoRequest,
    db: Session = Depends(get_db),
    _: None = Depends(RequirePermission("EDITAR_TERMO")),
):
    try:
        uid = uuid.UUID(id_depoimento)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de depoimento inválido.")

    termo = db.query(TermosFinais).filter(TermosFinais.id_depoimento == uid).first()
    if not termo:
        raise HTTPException(status_code=404, detail="Termo não encontrado para este depoimento.")

    termo.txt_editado_humano = payload.txt_editado_humano
    db.commit()
    db.refresh(termo)
    return termo
