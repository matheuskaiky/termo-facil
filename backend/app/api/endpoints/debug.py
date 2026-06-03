"""
Dev/Debug — módulo de comparação (benchmark) de modelos. Tudo aqui exige a
permissão ACESSAR_DEV_DEBUG. Os processamentos salvam EXATAMENTE a mesma carga de
dados que produção (ProcessamentoTeste espelha TermosFinais) e o detalhe é devolvido
na MESMA shape de GET /termos/{id}, para reusar o componente de auditoria read-only.
"""
import csv
import io
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import RequirePermission, get_current_user
from app.core import debug_models
from app.core.permissions import Permission
from app.db import get_db
from app.models import ProcessamentoTeste, TesteIA, Usuario
from app.services.storage_service import audio_storage

_MAGIC_AUDIO = (b"RIFF", b"ID3", b"\xff\xfb", b"\xff\xfa", b"OggS")
_MAX_AUDIO_BYTES = 200 * 1024 * 1024

# Routers gated by ACESSAR_DEV_DEBUG.
router = APIRouter(dependencies=[Depends(RequirePermission(Permission.ACESSAR_DEV_DEBUG))])
models_router = APIRouter(dependencies=[Depends(RequirePermission(Permission.ACESSAR_DEV_DEBUG))])


# ── Modelos disponíveis ─────────────────────────────────────────────────────────
@models_router.get("/available")
def models_available():
    """Catálogo de modelos para os comboboxes (inclui 'Não testar') + health-check."""
    return {"catalogo": debug_models.catalogo(), "health": debug_models.health_check()}


# ── Schemas ─────────────────────────────────────────────────────────────────────
class ProcessamentoCreate(BaseModel):
    asr_model: Optional[str] = None
    ner_model: Optional[str] = None
    llm_model: Optional[str] = None
    diarizacao: Optional[str] = "heuristic"


def _proc_resumo(p: ProcessamentoTeste) -> dict:
    """Linha compacta para a tabela comparativa."""
    n_entidades = len(p.ner_entidades or [])
    tam_transcricao = len(p.txt_literal_asr or "")
    return {
        "id_processamento": str(p.id_processamento),
        "asr_model": p.asr_model,
        "ner_model": p.ner_model,
        "llm_model": p.llm_model,
        "diarizacao": p.diarizacao,
        "status": p.status,
        "confianca_asr": p.confianca_asr,
        "confianca_ner": p.confianca_ner,
        "tempo_asr_ms": p.tempo_asr_ms,
        "tempo_ner_ms": p.tempo_ner_ms,
        "tempo_llm_ms": p.tempo_llm_ms,
        "tempo_total_ms": p.tempo_total_ms,
        "n_entidades": n_entidades,
        "tam_transcricao": tam_transcricao,
        "erro": p.erro,
        "data_criacao": p.data_criacao.isoformat() if p.data_criacao else None,
    }


def _teste_resumo(t: TesteIA) -> dict:
    return {
        "id_teste": str(t.id_teste),
        "nome": t.nome,
        "audio_filename": t.audio_filename,
        "data_criacao": t.data_criacao.isoformat() if t.data_criacao else None,
        "n_processamentos": len(t.processamentos or []),
    }


def _get_teste_or_404(db: Session, teste_id: str) -> TesteIA:
    try:
        tid = uuid.UUID(teste_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de teste inválido.")
    t = db.query(TesteIA).filter(TesteIA.id_teste == tid).first()
    if not t:
        raise HTTPException(status_code=404, detail="Teste não encontrado.")
    return t


# ── Testes ───────────────────────────────────────────────────────────────────────
@router.post("/testes", status_code=201)
async def criar_teste(
    nome: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Cria um Teste (nome + áudio). O áudio é subido no MinIO e reusado por todos os processamentos."""
    if not (file.filename or "").endswith((".wav", ".mp3", ".m4a", ".opus")):
        raise HTTPException(status_code=400, detail="Formato de áudio não suportado. Use .wav, .mp3, .m4a ou .opus.")

    content = b""
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        content += chunk
        if len(content) > _MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo excede o limite de 200 MB.")
    if len(content) < 12 or not any(content[:12].startswith(m) for m in _MAGIC_AUDIO):
        raise HTTPException(status_code=415, detail="Formato de áudio não reconhecido.")

    unique_filename = f"debug/{uuid.uuid4()}_{file.filename}"
    storage_path = audio_storage.upload_file(content, unique_filename)

    teste = TesteIA(
        nome=nome.strip(),
        storage_path_audio=storage_path,
        audio_filename=file.filename,
        id_usuario_criador=current_user.id_usuario,
    )
    db.add(teste)
    db.commit()
    db.refresh(teste)
    return _teste_resumo(teste)


@router.get("/testes")
def listar_testes(db: Session = Depends(get_db)):
    testes = db.query(TesteIA).order_by(TesteIA.data_criacao.desc()).all()
    return [_teste_resumo(t) for t in testes]


@router.get("/testes/{teste_id}")
def detalhe_teste(teste_id: str, db: Session = Depends(get_db)):
    t = _get_teste_or_404(db, teste_id)
    return {
        **_teste_resumo(t),
        "processamentos": [
            _proc_resumo(p)
            for p in sorted(t.processamentos or [], key=lambda x: x.data_criacao or x.id_processamento)
        ],
    }


# ── Processamentos ────────────────────────────────────────────────────────────────
@router.post("/testes/{teste_id}/processamentos", status_code=202)
def criar_processamento(teste_id: str, payload: ProcessamentoCreate, db: Session = Depends(get_db)):
    """Cria um Processamento (combinação de modelos) e dispara a task de execução."""
    t = _get_teste_or_404(db, teste_id)

    # ASR é obrigatório — sem transcrição não há nada a comparar.
    if debug_models.resolve_asr(payload.asr_model or "") is None:
        raise HTTPException(status_code=422, detail="Selecione um modelo de ASR (obrigatório).")

    proc = ProcessamentoTeste(
        id_teste=t.id_teste,
        asr_model=payload.asr_model,
        ner_model=payload.ner_model,
        llm_model=payload.llm_model,
        diarizacao=payload.diarizacao or "heuristic",
    )
    db.add(proc)
    db.commit()
    db.refresh(proc)

    from app.core.celery_app import celery_app
    celery_app.send_task("run_debug_processing", args=[str(proc.id_processamento)])

    return _proc_resumo(proc)


def _get_proc_or_404(db: Session, proc_id: str) -> ProcessamentoTeste:
    try:
        pid = uuid.UUID(proc_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de processamento inválido.")
    p = db.query(ProcessamentoTeste).filter(ProcessamentoTeste.id_processamento == pid).first()
    if not p:
        raise HTTPException(status_code=404, detail="Processamento não encontrado.")
    return p


@router.get("/processamentos/{proc_id}")
def detalhe_processamento(proc_id: str, db: Session = Depends(get_db)):
    """
    Detalhe na MESMA shape de GET /termos/{id} — para reuso da auditoria em modo
    read-only (`assinado=True` deixa a tela imutável). Inclui também os modelos usados
    e o status, para o contexto de debug.
    """
    p = _get_proc_or_404(db, proc_id)
    t = p.teste
    return {
        "id_depoimento": str(p.id_processamento),
        "txt_literal_asr": p.txt_literal_asr,
        "txt_original_ia": p.txt_original_ia,
        "txt_editado_humano": None,
        "dicionario_ner": p.dicionario_ner,
        "segmentos_asr": p.segmentos_asr,
        "ner_entidades": p.ner_entidades,
        "confianca_asr": p.confianca_asr,
        "confianca_ner": p.confianca_ner,
        "tempo_asr_ms": p.tempo_asr_ms,
        "tempo_ner_ms": p.tempo_ner_ms,
        "tempo_llm_ms": p.tempo_llm_ms,
        "tempo_total_ms": p.tempo_total_ms,
        "nome_depoente": t.nome if t else "Teste",
        "num_procedimento": f"DEBUG · {p.asr_model or '—'} / {p.ner_model or '—'} / {p.llm_model or '—'}",
        "assinado": True,  # auditoria read-only
        "status": p.status,
        "erro": p.erro,
        "modelos": {
            "asr": p.asr_model, "ner": p.ner_model,
            "llm": p.llm_model, "diarizacao": p.diarizacao,
        },
    }


# ── Exportação CSV ────────────────────────────────────────────────────────────────
_CSV_COLUMNS = [
    "id_processamento", "asr_model", "ner_model", "llm_model", "diarizacao", "status",
    "confianca_asr", "confianca_ner", "tempo_asr_ms", "tempo_ner_ms", "tempo_llm_ms",
    "tempo_total_ms", "n_entidades", "tam_transcricao", "data_criacao", "erro",
]


@router.get("/testes/{teste_id}/export.csv")
def exportar_csv(teste_id: str, db: Session = Depends(get_db)):
    """Dump tabular rico dos processamentos do teste — para o Dev plotar em ferramentas externas."""
    t = _get_teste_or_404(db, teste_id)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for p in sorted(t.processamentos or [], key=lambda x: x.data_criacao or x.id_processamento):
        writer.writerow(_proc_resumo(p))
    buffer.seek(0)
    safe = "".join(c if c.isalnum() else "_" for c in (t.nome or "teste"))
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="teste_{safe}.csv"'},
    )
