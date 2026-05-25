from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Depoimento, JobProcessamentoIA, StatusJob, TermosFinais
from app.api.deps import RequirePermission

# Baseline PIBITI: tempo médio estimado de redação manual por depoimento (horas)
_HORAS_POR_TERMO = 2.5

router = APIRouter(dependencies=[Depends(RequirePermission('VER_METRICAS'))])


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
