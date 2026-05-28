import logging
from contextlib import ExitStack

from app.core.celery_app import celery_app
from app.db import SessionLocal
from app.models import JobProcessamentoIA, StatusJob, TermosFinais
from app.services.storage_service import audio_storage, speaker_samples_storage
from app.services.asr_service import asr_model
from app.services.ner_service import ner_model
from app.services.llm_service import llm_model
from app.services.speaker_role_service import role_resolver

logger = logging.getLogger(__name__)


def _apply_role_mapping(segments: list[dict], mapping: dict[str, str]) -> list[dict]:
    if not mapping:
        return segments
    return [{**s, "speaker": mapping.get(s["speaker"], s["speaker"])} for s in segments]


def _download_speaker_samples(codec_info: dict) -> tuple["ExitStack", dict[str, str]]:
    """Downloads speaker sample files from MinIO into temp files.
    Returns (stack, {role: local_path}). Caller must close the stack."""
    stack = ExitStack()
    local_samples: dict[str, str] = {}
    raw_samples: dict[str, str] = (codec_info or {}).get("speaker_samples", {})
    for role, storage_key in raw_samples.items():
        try:
            local_path = stack.enter_context(
                speaker_samples_storage.download_as_local_file(storage_key)
            )
            local_samples[role] = local_path
        except Exception as exc:
            logger.warning("[ROLE] Could not download sample role=%s: %s", role, exc)
    return stack, local_samples


@celery_app.task(name="process_audio", time_limit=3600, soft_time_limit=3300)
def process_audio_task(job_id: str):
    """
    Full ASR -> Speaker Role Resolution -> NER -> LLM processing pipeline.
    """
    logger.info("Iniciando processamento do Job ID: %s", job_id)

    db = SessionLocal()
    job = None
    try:
        job = db.query(JobProcessamentoIA).filter(JobProcessamentoIA.id_job == job_id).first()
        if not job:
            logger.error("Job %s not found in database.", job_id)
            return False

        midia = job.depoimento.midia_bruta
        if not midia:
            logger.error("Nenhuma mídia encontrada para o Job %s.", job_id)
            job.status = StatusJob.ERRO
            db.commit()
            return False

        job.status = StatusJob.TRANSCREVENDO
        db.commit()

        # 1. ASR — Whisper returns [{start, end, text, speaker}, ...]
        logger.info("Running ASR (Whisper)...")
        with audio_storage.download_as_local_file(midia.storage_path) as local_audio:

            segments = asr_model.transcribe(local_audio, language="pt")

            # 2. Speaker role resolution — relabels speakers when needed
            samples_stack, local_samples = _download_speaker_samples(midia.codec_info or {})
            with samples_stack:
                role_mapping = role_resolver.resolve(
                    segments,
                    audio_path=local_audio if local_samples else None,
                    known_samples=local_samples or None,
                )
            segments = _apply_role_mapping(segments, role_mapping)

        # Plain text joined from segments — used by NER and LLM
        transcript = " ".join(seg["text"] for seg in segments)

        # 3. NER — LeNER-Br (operates on plain text)
        job.status = StatusJob.EXTRAINDO_DADOS
        db.commit()
        logger.info("Extracting Entities (LeNER-Br)...")
        entities = ner_model.extract_entities(transcript)

        # 4. LLM — Síntese jurídica ancorada nas entidades NER
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
        logger.info("Job %s finalizado com sucesso!", job_id)
        return True

    except Exception as e:
        logger.error("Error processing Job %s: %s", job_id, str(e))
        db.rollback()
        if job:
            job.status = StatusJob.ERRO
            existing_params = job.parametros_ia or {}
            job.parametros_ia = {**existing_params, "erro": str(e)}
            try:
                db.commit()
            except Exception as commit_error:
                logger.error("Failed to commit error state for Job %s: %s", job_id, str(commit_error))
                db.rollback()
        return False

    finally:
        db.close()
