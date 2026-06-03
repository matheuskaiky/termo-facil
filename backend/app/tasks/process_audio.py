import logging
import os
import time
from contextlib import ExitStack

from app.core.celery_app import celery_app
from app.db import SessionLocal
from app.models import JobProcessamentoIA, StatusJob, TermosFinais
from app.services.storage_service import audio_storage, speaker_samples_storage
from app.services.asr_service import asr_model
from app.services.ner_service import ner_model
from app.services.llm_service import llm_model
from app.services.speaker_role_service import role_resolver
from app.services.diarization_service import build_diarizer

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


def _cleanup_separated_files(separated: dict[str, str]) -> None:
    """Deletes temporary separated audio files. Silent on errors."""
    for path in separated.values():
        try:
            os.unlink(path)
        except OSError:
            pass


def run_pipeline(
    local_audio: str,
    *,
    asr,
    ner,
    llm,
    diarizer=None,
    role_resolver_obj=None,
    codec_info: dict | None = None,
    skip_ner: bool = False,
    skip_llm: bool = False,
    status_cb=None,
) -> dict:
    """
    Núcleo único do pipeline (ASR → resolução de papel → NER → LLM), com cronometragem
    por etapa. Reusado pela task de produção e pela task de Dev/Debug — é a garantia de
    que um processamento de teste gera EXATAMENTE a mesma carga de dados que produção.

    `local_audio` já é um caminho local (o chamador faz o download). `skip_ner`/`skip_llm`
    pulam a etapa (módulo Dev/Debug). `status_cb(StatusJob)` é opcional (atualiza status).
    Retorna um dict com transcript/segments/entities/ner_entidades/summary/confianças/tempos.
    """
    role_resolver_obj = role_resolver_obj or role_resolver

    def _status(stage: StatusJob) -> None:
        if status_cb:
            status_cb(stage)

    # ── 1. ASR (+ separação opcional) ───────────────────────────────────────────
    _status(StatusJob.TRANSCREVENDO)
    logger.info("Running ASR...")
    t_asr0 = time.perf_counter()
    if diarizer is not None:
        logger.info("Using PixIT separation pipeline.")
        separated_audios = diarizer.diarize_and_separate(local_audio)
        try:
            segments = asr.transcribe_separated(separated_audios)
        finally:
            _cleanup_separated_files(separated_audios)
    else:
        logger.info("Using heuristic diarization.")
        segments = asr.transcribe(local_audio, language="pt")
    tempo_asr_ms = round((time.perf_counter() - t_asr0) * 1000, 1)

    # ── 2. Resolução de papel do falante ────────────────────────────────────────
    samples_stack, local_samples = _download_speaker_samples(codec_info or {})
    with samples_stack:
        role_mapping = role_resolver_obj.resolve(
            segments,
            audio_path=local_audio if local_samples else None,
            known_samples=local_samples or None,
        )
    segments = _apply_role_mapping(segments, role_mapping)

    transcript = " ".join(seg["text"] for seg in segments)

    # ── 3. NER ──────────────────────────────────────────────────────────────────
    if skip_ner:
        entities, ner_entidades, tempo_ner_ms = {}, [], None
    else:
        _status(StatusJob.EXTRAINDO_DADOS)
        logger.info("Extracting Entities (LeNER-Br)...")
        t_ner0 = time.perf_counter()
        entities, ner_entidades = ner.extract_entities_scored(transcript)
        tempo_ner_ms = round((time.perf_counter() - t_ner0) * 1000, 1)

    # ── 4. LLM ──────────────────────────────────────────────────────────────────
    if skip_llm:
        summary, tempo_llm_ms = None, None
    else:
        _status(StatusJob.GERANDO_RESUMO)
        logger.info("Generating Deterministic Legal Summary (LLM)...")
        t_llm0 = time.perf_counter()
        summary = llm.synthesize(transcript, entities=entities)
        tempo_llm_ms = round((time.perf_counter() - t_llm0) * 1000, 1)

    # Confiança média (0–100, 1 casa) — estimativa para o revisor.
    seg_confs = [s["confianca"] for s in segments if s.get("confianca") is not None]
    confianca_asr = round(sum(seg_confs) / len(seg_confs), 1) if seg_confs else None
    ent_scores = [e["score"] for e in ner_entidades if e.get("score") is not None]
    confianca_ner = round(sum(ent_scores) / len(ent_scores), 1) if ent_scores else None

    tempo_total_ms = round(
        sum(t for t in (tempo_asr_ms, tempo_ner_ms, tempo_llm_ms) if t is not None), 1
    )

    return {
        "segments": segments,
        "transcript": transcript,
        "entities": entities,
        "ner_entidades": ner_entidades,
        "summary": summary,
        "confianca_asr": confianca_asr,
        "confianca_ner": confianca_ner,
        "tempo_asr_ms": tempo_asr_ms,
        "tempo_ner_ms": tempo_ner_ms,
        "tempo_llm_ms": tempo_llm_ms,
        "tempo_total_ms": tempo_total_ms,
    }


@celery_app.task(name="process_audio", time_limit=3600, soft_time_limit=3300)
def process_audio_task(job_id: str):
    """
    Full pipeline (produção): ASR (+ optional PixIT separation) → Speaker Role
    Resolution → NER → LLM. Delega o núcleo a run_pipeline() e persiste em TermosFinais.
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

        def _set_status(stage: StatusJob) -> None:
            job.status = stage
            db.commit()

        with audio_storage.download_as_local_file(midia.storage_path) as local_audio:
            result = run_pipeline(
                local_audio,
                asr=asr_model,
                ner=ner_model,
                llm=llm_model,
                diarizer=build_diarizer(),
                codec_info=midia.codec_info or {},
                status_cb=_set_status,
            )

        # Reprocessamento: remove TermosFinais pré-existente deste depoimento.
        db.query(TermosFinais).filter(
            TermosFinais.id_depoimento == job.id_depoimento
        ).delete(synchronize_session=False)

        resultado_final = TermosFinais(
            id_depoimento=job.id_depoimento,
            id_job=job.id_job,
            txt_literal_asr=result["transcript"],
            txt_original_ia=result["summary"],
            dicionario_ner=result["entities"],
            ner_entidades=result["ner_entidades"],
            segmentos_asr=result["segments"],
            confianca_asr=result["confianca_asr"],
            confianca_ner=result["confianca_ner"],
            tempo_asr_ms=result["tempo_asr_ms"],
            tempo_ner_ms=result["tempo_ner_ms"],
            tempo_llm_ms=result["tempo_llm_ms"],
            tempo_total_ms=result["tempo_total_ms"],
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
