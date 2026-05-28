import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_

from app.core.celery_app import celery_app
from app.db import SessionLocal
from app.models import MidiaBruta, TermosFinais
from app.services.storage_service import audio_storage

logger = logging.getLogger(__name__)


@celery_app.task(name="expurgo_dados_expirados")
def expurgo_dados_expirados():
    """
    Safety-net LGPD (RN-04): expurges audio and clears NER/ASR data for
    records whose PDF was exported more than 24 h ago. Runs hourly via
    Celery Beat as a fallback for cases where the immediate delete in
    pdf.py failed (e.g. transient MinIO network error).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    db = SessionLocal()
    deleted_audio = 0
    cleaned_termos = 0

    try:
        # --- Step 1: delete raw audio from MinIO ---
        midias = (
            db.query(MidiaBruta)
            .join(TermosFinais, TermosFinais.id_depoimento == MidiaBruta.id_depoimento)
            .filter(
                TermosFinais.data_exportacao_pdf.isnot(None),
                TermosFinais.data_exportacao_pdf < cutoff,
                MidiaBruta.storage_path.isnot(None),
            )
            .all()
        )
        for midia in midias:
            try:
                audio_storage.delete_file(midia.storage_path)
                midia.storage_path = None
                deleted_audio += 1
                logger.info("[EXPURGO-LGPD] Áudio removido: depoimento=%s", midia.id_depoimento)
            except Exception as exc:
                logger.error(
                    "[EXPURGO-LGPD] Falha ao remover áudio depoimento=%s: %s",
                    midia.id_depoimento,
                    exc,
                )

        # --- Step 2: clear residual NER/segments from DB ---
        termos_list = (
            db.query(TermosFinais)
            .filter(
                TermosFinais.data_exportacao_pdf.isnot(None),
                TermosFinais.data_exportacao_pdf < cutoff,
                or_(
                    TermosFinais.dicionario_ner.isnot(None),
                    TermosFinais.segmentos_asr.isnot(None),
                ),
            )
            .all()
        )
        for t in termos_list:
            t.dicionario_ner = None
            t.segmentos_asr = None
            cleaned_termos += 1
            logger.info("[EXPURGO-LGPD] NER/segmentos limpos: depoimento=%s", t.id_depoimento)

        db.commit()
        logger.info(
            "[EXPURGO-LGPD] Ciclo concluído — áudios removidos: %d, termos limpos: %d",
            deleted_audio,
            cleaned_termos,
        )

    except Exception as exc:
        logger.error("[EXPURGO-LGPD] Erro crítico no ciclo de expurgo: %s", exc)
        db.rollback()
    finally:
        db.close()
