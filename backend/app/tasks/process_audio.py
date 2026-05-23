import logging
from app.core.celery_app import celery_app
from app.db import SessionLocal
from app.models import JobProcessamentoIA, StatusJob, TermosFinais
from app.services.storage_service import audio_storage
from app.services.asr_service import asr_model

logger = logging.getLogger(__name__)

mock_llm = (
    "Aos costumes, disse chamar-se Carlos Eduardo Alves. Inquirido pela autoridade policial "
    "acerca dos fatos ocorridos na data de ontem, por volta das 22h00min, respondeu que se "
    "encontrava na praça central desta urbe, momento em que avistou dois indivíduos trafegando "
    "em alta velocidade em uma motocicleta de cor preta, cuja placa ostentava o alfanumérico "
    "parcial ABC-1234. Relatou ainda que o indivíduo que ocupava a garupa trajava jaqueta "
    "vermelha e aparentemente portava arma de fogo de cor preta."
)
mock_ner = {
    "PESSOAS": ["Carlos Eduardo Alves"],
    "LOCAIS": ["Praça central"],
    "VEICULOS": ["Moto preta", "Placa ABC-1234"],
    "OBJETOS_CRIME": ["Jaqueta vermelha", "Arma preta"]
}

@celery_app.task(name="process_audio")
def process_audio_task(job_id: str):
    """
    ASR -> NER -> LLM processing pipeline.
    NER (step 4) and LLM (step 5) are mocked — see Issues #12 and #11.
    """
    logger.info(f"Iniciando processamento do Job ID: {job_id}")

    db = SessionLocal()
    job = None
    try:
        # 1. Fetch the Job record
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

        # 2. Update Status to Processando
        job.status = StatusJob.PROCESSANDO
        db.commit()

        # 3. ASR — Whisper
        logger.info("Running ASR (Whisper)...")
        with audio_storage.download_as_local_file(midia.storage_path) as local_path:
            transcript = asr_model.transcribe(local_path, language="pt")

        # 4. NER — LeNER-Br (mock, Issue #12)
        logger.info("Extracting Entities (LeNER-Br)...")
        entities = mock_ner

        # 5. LLM — Síntese jurídica (mock, Issue #11)
        logger.info("Generating Deterministic Legal Summary (LLM)...")
        summary = mock_llm

        resultado_final = TermosFinais(
            id_depoimento=job.id_depoimento,
            id_job=job.id_job,
            txt_literal_asr=transcript,
            txt_original_ia=summary,
            dicionario_ner=entities,
            txt_editado_humano=None,
            assinatura_digital=None,
            hash_pdf=None
        )

        db.add(resultado_final)

        # 6. Mark as successful
        job.status = StatusJob.CONCLUIDO
        db.commit()
        logger.info(f"Job {job_id} finalizado com sucesso!")

        return True

    except Exception as e:
        logger.error(f"Error processing Job {job_id}: {str(e)}")
        if job:
            job.status = StatusJob.ERRO
            db.commit()
        return False

    finally:
        db.close()
