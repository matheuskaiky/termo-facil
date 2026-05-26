import logging
from app.core.celery_app import celery_app
from app.db import SessionLocal
from app.models import JobProcessamentoIA, StatusJob, TermosFinais
from app.services.storage_service import audio_storage
from app.services.asr_service import asr_model
from app.services.ner_service import ner_model
from app.services.llm_service import llm_model

logger = logging.getLogger(__name__)


@celery_app.task(name="process_audio", time_limit=3600, soft_time_limit=3300)
def process_audio_task(job_id: str):
    """
    Full ASR -> NER -> LLM processing pipeline.
    ASR now returns time-stamped segments with speaker labels.
    Plain text is extracted from segments for NER and LLM.
    """
    logger.info(f"Iniciando processamento do Job ID: {job_id}")

    db = SessionLocal()
    job = None
    try:
        job = db.query(JobProcessamentoIA).filter(JobProcessamentoIA.id_job == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return False

        midia = job.depoimento.midia_bruta
        if not midia:
            logger.error(f"Nenhuma mídia encontrada para o Job {job_id}.")
            job.status = StatusJob.ERRO
            db.commit()
            return False

        job.status = StatusJob.TRANSCREVENDO
        db.commit()

        # 3. ASR — Whisper returns [{start, end, text, speaker}, ...]
        logger.info("Running ASR (Whisper)...")
        with audio_storage.download_as_local_file(midia.storage_path) as local_path:
            segments = asr_model.transcribe(local_path, language="pt")

        # Plain text joined from segments — used by NER and LLM
        transcript = " ".join(seg["text"] for seg in segments)

        # 4. NER — LeNER-Br (operates on plain text)
        job.status = StatusJob.EXTRAINDO_DADOS
        db.commit()
        logger.info("Extracting Entities (LeNER-Br)...")
        entities = ner_model.extract_entities(transcript)

        # 5. LLM — Síntese jurídica ancorada nas entidades NER
        job.status = StatusJob.GERANDO_RESUMO
        db.commit()
        logger.info("Generating Deterministic Legal Summary (LLM)...")
        summary = llm_model.synthesize(transcript, entities=entities)

        resultado_final = TermosFinais(
            id_depoimento=job.id_depoimento,
            id_job=job.id_job,
            txt_literal_asr=transcript,
            txt_original_ia=summary,
            dicionario_ner=entities,
            segmentos_asr=segments,
            txt_editado_humano=None,
            assinatura_digital=None,
            hash_pdf=None,
        )

        db.add(resultado_final)
        job.status = StatusJob.CONCLUIDO
        db.commit()
        logger.info(f"Job {job_id} finalizado com sucesso!")
        return True

    except Exception as e:
        logger.error(f"Error processing Job {job_id}: {str(e)}")
        if job:
            job.status = StatusJob.ERRO
            existing_params = job.parametros_ia or {}
            job.parametros_ia = {**existing_params, "erro": str(e)}
            db.commit()
        return False

    finally:
        db.close()
