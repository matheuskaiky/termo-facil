"""
Dev/Debug — task que executa o pipeline parametrizado (combinação de modelos) sobre
o áudio de um Teste e persiste EXATAMENTE a mesma carga de dados que produção em
ProcessamentoTeste. Reusa o núcleo `run_pipeline` (process_audio.py) — é o que garante
a paridade produção ↔ debug.
"""
import logging

from app.core.celery_app import celery_app
from app.core import debug_models
from app.db import SessionLocal
from app.models import ProcessamentoTeste, StatusJob
from app.services.storage_service import audio_storage
from app.services.asr_service import build_asr
from app.services.ner_service import build_ner
from app.services.llm_service import build_llm
from app.services.diarization_service import build_diarizer_for
from app.tasks.process_audio import run_pipeline

logger = logging.getLogger(__name__)


@celery_app.task(name="run_debug_processing", time_limit=3600, soft_time_limit=3300)
def run_debug_processing(processamento_id: str):
    """Roda a combinação de modelos de um ProcessamentoTeste; 'Não testar' (skip) pula a etapa."""
    logger.info("Iniciando processamento de teste: %s", processamento_id)
    db = SessionLocal()
    proc = None
    try:
        proc = (
            db.query(ProcessamentoTeste)
            .filter(ProcessamentoTeste.id_processamento == processamento_id)
            .first()
        )
        if not proc:
            logger.error("Processamento de teste %s não encontrado.", processamento_id)
            return False

        teste = proc.teste
        if not teste or not teste.storage_path_audio:
            proc.status = StatusJob.ERRO
            proc.erro = "Áudio do teste ausente."
            db.commit()
            return False

        # Resolve a combinação de modelos a partir do catálogo (separado da produção).
        asr_size = debug_models.resolve_asr(proc.asr_model)
        ner_name = debug_models.resolve_ner(proc.ner_model)
        llm_name = debug_models.resolve_llm(proc.llm_model)
        diar = debug_models.resolve_diarizacao(proc.diarizacao or "heuristic")

        # ASR é obrigatório — sem transcrição não há nada a comparar.
        if asr_size is None:
            proc.status = StatusJob.ERRO
            proc.erro = "ASR é obrigatório: selecione um modelo de transcrição."
            db.commit()
            return False

        skip_ner = ner_name is None
        skip_llm = llm_name is None

        asr = build_asr(asr_size)
        ner = build_ner(ner_name) if not skip_ner else None
        llm = build_llm(llm_name) if not skip_llm else None
        diarizer = build_diarizer_for(diar)

        def _set_status(stage: StatusJob) -> None:
            proc.status = stage
            db.commit()

        with audio_storage.download_as_local_file(teste.storage_path_audio) as local_audio:
            result = run_pipeline(
                local_audio,
                asr=asr,
                ner=ner,
                llm=llm,
                diarizer=diarizer,
                codec_info=None,
                skip_ner=skip_ner,
                skip_llm=skip_llm,
                status_cb=_set_status,
            )

        proc.txt_literal_asr = result["transcript"]
        proc.txt_original_ia = result["summary"]
        proc.dicionario_ner = result["entities"]
        proc.ner_entidades = result["ner_entidades"]
        proc.segmentos_asr = result["segments"]
        proc.confianca_asr = result["confianca_asr"]
        proc.confianca_ner = result["confianca_ner"]
        proc.tempo_asr_ms = result["tempo_asr_ms"]
        proc.tempo_ner_ms = result["tempo_ner_ms"]
        proc.tempo_llm_ms = result["tempo_llm_ms"]
        proc.tempo_total_ms = result["tempo_total_ms"]
        proc.erro = None
        proc.status = StatusJob.CONCLUIDO
        db.commit()
        logger.info("Processamento de teste %s finalizado.", processamento_id)
        return True

    except Exception as e:
        logger.error("Erro no processamento de teste %s: %s", processamento_id, str(e))
        db.rollback()
        if proc:
            proc.status = StatusJob.ERRO
            proc.erro = str(e)
            try:
                db.commit()
            except Exception:
                db.rollback()
        return False

    finally:
        db.close()
