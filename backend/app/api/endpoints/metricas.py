import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    Depoimento, JobProcessamentoIA, StatusJob, TermosFinais,
    Delegacia, Inquerito, Usuario,
)
from app.api.deps import RequirePermission
from app.core.permissions import Permission

# Baseline PIBITI: tempo médio estimado de redação manual por depoimento (horas)
_HORAS_POR_TERMO = 2.5

router = APIRouter(dependencies=[Depends(RequirePermission(Permission.VER_METRICAS))])


@router.get("")
def get_metricas(db: Session = Depends(get_db)):
    """
    Aggregated system metrics for strategic oversight (RF-07).
    Returns only counts and statistics — zero sensitive content.
    """
    total_depoimentos = db.query(func.count(Depoimento.id_depoimento)).scalar() or 0

    total_termos = db.query(func.count(TermosFinais.id_depoimento)).scalar() or 0

    total_pdfs = (
        db.query(func.count(TermosFinais.id_depoimento))
        .filter(TermosFinais.hash_pdf.isnot(None))
        .scalar() or 0
    )

    jobs_result = (
        db.query(JobProcessamentoIA.status, func.count(JobProcessamentoIA.id_job).label("total"))
        .group_by(JobProcessamentoIA.status)
        .all()
    )
    jobs_por_status: dict[str, int] = {s.value: 0 for s in StatusJob}
    for row in jobs_result:
        jobs_por_status[row.status] = row.total

    total_finalizados = jobs_por_status.get("Concluído", 0) + jobs_por_status.get("Erro", 0)
    taxa_sucesso = round(
        (jobs_por_status.get("Concluído", 0) / total_finalizados * 100) if total_finalizados > 0 else 0.0,
        1,
    )

    return {
        "total_depoimentos": total_depoimentos,
        "total_termos_gerados": total_termos,
        "total_pdfs_exportados": total_pdfs,
        "jobs_por_status": jobs_por_status,
        "taxa_sucesso_pct": taxa_sucesso,
        "horas_economizadas_estimadas": round(total_pdfs * _HORAS_POR_TERMO, 1),
    }


@router.get("/por-delegacia")
def metricas_por_delegacia(db: Session = Depends(get_db)):
    """Total de depoimentos (não descartados) por delegacia — para o overview."""
    rows = (
        db.query(
            Delegacia.id_delegacia,
            Delegacia.nome_unidade,
            Delegacia.sigla,
            func.count(Depoimento.id_depoimento).filter(Depoimento.descartado.is_(False)).label("total"),
        )
        .outerjoin(Inquerito, Inquerito.id_delegacia == Delegacia.id_delegacia)
        .outerjoin(Depoimento, Depoimento.id_inquerito == Inquerito.id_inquerito)
        .group_by(Delegacia.id_delegacia, Delegacia.nome_unidade, Delegacia.sigla)
        .order_by(func.count(Depoimento.id_depoimento).desc())
        .all()
    )
    return [
        {"id_delegacia": str(r.id_delegacia), "nome_unidade": r.nome_unidade, "sigla": r.sigla, "total": r.total or 0}
        for r in rows
    ]


def _taxa_sucesso(concluidos: int, erros: int) -> float:
    finalizados = concluidos + erros
    return round((concluidos / finalizados * 100) if finalizados else 0.0, 1)


@router.get("/delegacias/{id_delegacia}")
def metricas_delegacia_detail(id_delegacia: str, db: Session = Depends(get_db)):
    """Detalhe agregado de uma delegacia (consumido pelo dashboard de detalhe)."""
    try:
        did = uuid.UUID(id_delegacia)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de delegacia inválido.")
    deleg = db.query(Delegacia).filter(Delegacia.id_delegacia == did).first()
    if not deleg:
        raise HTTPException(status_code=404, detail="Delegacia não encontrada.")

    # Depoimentos não descartados desta delegacia (via inquérito).
    base = (
        db.query(Depoimento)
        .join(Inquerito, Depoimento.id_inquerito == Inquerito.id_inquerito)
        .filter(Inquerito.id_delegacia == did, Depoimento.descartado.is_(False))
    )
    total_depoimentos = base.count()
    servidores_ativos = (
        db.query(func.count(Usuario.id_usuario))
        .filter(Usuario.id_delegacia == did, Usuario.ativo.is_(True))
        .scalar() or 0
    )

    # Taxa de sucesso a partir dos jobs dos depoimentos desta delegacia.
    job_status_rows = (
        db.query(JobProcessamentoIA.status, func.count(JobProcessamentoIA.id_job))
        .join(Depoimento, JobProcessamentoIA.id_depoimento == Depoimento.id_depoimento)
        .join(Inquerito, Depoimento.id_inquerito == Inquerito.id_inquerito)
        .filter(Inquerito.id_delegacia == did)
        .group_by(JobProcessamentoIA.status)
        .all()
    )
    status_counts = {s: c for s, c in job_status_rows}
    taxa = _taxa_sucesso(status_counts.get(StatusJob.CONCLUIDO.value, 0), status_counts.get(StatusJob.ERRO.value, 0))

    # Escrivães: depoimentos por usuário.
    escrivao_rows = (
        db.query(Usuario.id_usuario, Usuario.nome, func.count(Depoimento.id_depoimento))
        .join(Depoimento, Depoimento.id_usuario == Usuario.id_usuario)
        .join(Inquerito, Depoimento.id_inquerito == Inquerito.id_inquerito)
        .filter(Inquerito.id_delegacia == did, Depoimento.descartado.is_(False))
        .group_by(Usuario.id_usuario, Usuario.nome)
        .order_by(func.count(Depoimento.id_depoimento).desc())
        .all()
    )
    escrivaes = [
        {"id_usuario": str(uid), "nome": nome, "total": tot, "taxa": taxa}
        for uid, nome, tot in escrivao_rows
    ]

    # Tipos de depoente.
    tipo_rows = (
        db.query(Depoimento.tipo_depoente, func.count(Depoimento.id_depoimento))
        .join(Inquerito, Depoimento.id_inquerito == Inquerito.id_inquerito)
        .filter(Inquerito.id_delegacia == did, Depoimento.descartado.is_(False))
        .group_by(Depoimento.tipo_depoente)
        .all()
    )
    tipos_depoente = [{"tipo": t, "count": c} for t, c in tipo_rows]

    # Atividade recente.
    recentes = base.order_by(Depoimento.data_hora_reg.desc()).limit(8).all()
    atividade_recente = []
    for d in recentes:
        ultimo = max(d.jobs, key=lambda j: j.data_criacao) if d.jobs else None
        atividade_recente.append({
            "id_depoimento": str(d.id_depoimento),
            "num_procedimento": d.inquerito.num_procedimento if d.inquerito else "N/A",
            "nome_depoente": d.depoente.nome_depoente if d.depoente else "N/A",
            "escrivao": d.usuario.nome if d.usuario else "N/A",
            "status": (ultimo.status if ultimo else "Sem Upload"),
            "quando": d.data_hora_reg.isoformat() if d.data_hora_reg else None,
        })

    return {
        "id_delegacia": str(deleg.id_delegacia),
        "nome_unidade": deleg.nome_unidade,
        "sigla": deleg.sigla,
        "total_depoimentos": total_depoimentos,
        "servidores_ativos": servidores_ativos,
        "taxa_sucesso_pct": taxa,
        "tempo_medio_min": 0,  # duração de processamento não é registrada no schema atual
        "escrivaes": escrivaes,
        "tipos_depoente": tipos_depoente,
        "atividade_recente": atividade_recente,
    }
