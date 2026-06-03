from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import List, Any
import logging
import uuid
from app.db import get_db
from app.models import Depoimento, Inquerito, Depoente, Usuario, JobProcessamentoIA, StatusJob, TipoDepoente
from app.api.deps import get_current_user, RequirePermission
from app.schemas.processo import NovoProcessoPayload
from app.core.permissions import Permission
from app.utils.query_scopes import apply_depoimento_scope
from app.utils.cpf_utils import cpf_valido, digits

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def listar_processos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    descartados: str = Query(default="excluir", pattern="^(excluir|incluir|apenas)$"),
) -> Any:
    """
    Lista os depoimentos (processos) com paginação e escopo por cargo.
    `descartados`: excluir (padrão, esconde descartados) | incluir | apenas.
    Retorna também `descartados` (contagem no escopo) para o KPI.
    """
    base = db.query(Depoimento).options(
        joinedload(Depoimento.inquerito),
        joinedload(Depoimento.depoente),
        joinedload(Depoimento.usuario),
        joinedload(Depoimento.jobs)
    )
    base = apply_depoimento_scope(base, current_user)

    # Contagem de descartados no escopo (para o KPI), independente do filtro.
    descartados_count = base.filter(Depoimento.descartado.is_(True)).count()

    query = base
    if descartados == "excluir":
        query = query.filter(Depoimento.descartado.is_(False))
    elif descartados == "apenas":
        query = query.filter(Depoimento.descartado.is_(True))

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
            "status_job": job_status,
            "descartado": bool(d.descartado),
        })

    return {"total": total, "descartados": descartados_count, "items": resultados}


@router.get("/check-cpf")
def check_cpf(
    cpf: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Any:
    """Valida o CPF e indica se já existe um depoente cadastrado (autofill)."""
    if not cpf_valido(cpf):
        return {"valido": False, "existe": False, "nome_depoente": None}
    dep = db.query(Depoente).filter(Depoente.cpf == digits(cpf)).first()
    return {
        "valido": True,
        "existe": dep is not None,
        "nome_depoente": dep.nome_depoente if dep else None,
    }


@router.put("/{id_depoimento}/descartar")
def descartar_processo(
    id_depoimento: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Any:
    """
    Descarta um processo (soft-delete): mantém no registro, apenas marca como
    descartado. Respeita o escopo de visibilidade do usuário.
    """
    try:
        uid = uuid.UUID(id_depoimento)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de processo inválido.")

    scoped = apply_depoimento_scope(db.query(Depoimento), current_user)
    dep = scoped.filter(Depoimento.id_depoimento == uid).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")

    from app.utils.lock import assert_not_signed
    assert_not_signed(db, uid)

    dep.descartado = True
    dep.data_descarte = datetime.utcnow()
    dep.id_usuario_descarte = current_user.id_usuario
    db.commit()
    return {"id_depoimento": str(dep.id_depoimento), "descartado": True}

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

        endereco = {
            "cep": payload.cep,
            "logradouro": payload.logradouro,
            "numero": payload.numero,
            "complemento": payload.complemento,
            "bairro": payload.bairro,
            "municipio": payload.municipio,
            "uf": payload.uf,
            "cod_ibge": payload.cod_ibge,
        }

        if not depoente:
            depoente = Depoente(
                cpf=payload.cpf_depoente,
                nome_depoente=payload.nome_depoente,
                **endereco,
            )
            db.add(depoente)
            db.flush()
        else:
            # Atualiza o endereço do depoente existente quando informado.
            for field, value in endereco.items():
                if value:
                    setattr(depoente, field, value)

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
