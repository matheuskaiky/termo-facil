from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List, Any
import logging
from app.db import get_db
from app.models import Depoimento, Inquerito, Depoente, Usuario, JobProcessamentoIA, StatusJob, TipoDepoente
from app.api.deps import get_current_user, RequirePermission
from app.schemas.processo import NovoProcessoPayload
from app.core.permissions import Permission
from app.utils.query_scopes import apply_depoimento_scope

logger = logging.getLogger(__name__)

router = APIRouter()


def _validar_cpf(cpf: str) -> bool:
    """Valida CPF usando algoritmo dos dígitos verificadores."""
    cpf_clean = cpf.replace(".", "").replace("-", "")

    if not cpf_clean.isdigit() or len(cpf_clean) != 11:
        return False

    if cpf_clean == cpf_clean[0] * 11:
        return False

    def calc_digit(s: str, multiplier: int) -> int:
        total = sum(int(digit) * (multiplier - i) for i, digit in enumerate(s))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    d1 = calc_digit(cpf_clean[:9], 10)
    d2 = calc_digit(cpf_clean[:9] + str(d1), 11)

    return cpf_clean[9] == str(d1) and cpf_clean[10] == str(d2)

@router.get("/")
def listar_processos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
) -> Any:
    """
    Lista os depoimentos (processos) com paginação.
    Filtra por id_usuario se o cargo for 'Escrivão'.
    Filtra por delegacia se for 'Delegado'.
    Retorna tudo se for 'Admin' / 'Gestor Estratégico'.
    """
    query = db.query(Depoimento).options(
        joinedload(Depoimento.inquerito),
        joinedload(Depoimento.depoente),
        joinedload(Depoimento.usuario),
        joinedload(Depoimento.jobs)
    )
    query = apply_depoimento_scope(query, current_user)

    total = query.count()
    depoimentos = query.order_by(Depoimento.data_hora_reg.desc()).offset(offset).limit(limit).all()

    resultados = []
    for d in depoimentos:
        ultimo_job = max(d.jobs, key=lambda j: j.data_criacao) if d.jobs else None
        job_status = ultimo_job.status if ultimo_job else "Sem Upload"
        resultados.append({
            "id_depoimento": str(d.id_depoimento),
            "num_procedimento": d.inquerito.num_procedimento if d.inquerito else "N/A",
            "nome_depoente": d.depoente.nome_depoente if d.depoente else "N/A",
            "tipo_depoente": d.tipo_depoente,
            "data_hora_reg": d.data_hora_reg.isoformat() if d.data_hora_reg else None,
            "escrivao": d.usuario.nome if d.usuario else "N/A",
            "status_job": job_status
        })

    return {"total": total, "items": resultados}

@router.post("/novo")
def criar_processo(
    payload: NovoProcessoPayload,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RequirePermission(Permission.CRIAR_TERMO))
) -> Any:
    """
    Cria um novo Depoimento com Inquérito e Depoente (upsert).
    - Se num_procedimento não existe, cria novo Inquérito
    - Se CPF não existe, cria novo Depoente
    - Cria novo Depoimento associado ao usuário atual
    """
    try:
        inquerito = db.query(Inquerito).filter(
            Inquerito.num_procedimento == payload.num_procedimento
        ).first()

        if not inquerito:
            inquerito = Inquerito(
                id_delegacia=current_user.id_delegacia,
                num_procedimento=payload.num_procedimento,
                data_instauracao=payload.data_instauracao
            )
            db.add(inquerito)
            db.flush()

        depoente = db.query(Depoente).filter(
            Depoente.cpf == payload.cpf_depoente
        ).first()

        if not depoente:
            depoente = Depoente(
                cpf=payload.cpf_depoente,
                nome_depoente=payload.nome_depoente
            )
            db.add(depoente)
            db.flush()

        novo_depoimento = Depoimento(
            id_inquerito=inquerito.id_inquerito,
            id_usuario=current_user.id_usuario,
            id_depoente=depoente.id_depoente,
            tipo_depoente=payload.tipo_depoente
        )
        db.add(novo_depoimento)
        db.commit()
        db.refresh(novo_depoimento)

        return {"id_depoimento": str(novo_depoimento.id_depoimento)}

    except Exception as e:
        db.rollback()
        logger.exception("Erro ao criar processo")
        raise HTTPException(status_code=500, detail="Erro interno. Contate o administrador.")
