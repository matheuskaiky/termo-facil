import time
import logging
from app.core.celery_app import celery_app
from app.db import SessionLocal
from app.models import JobProcessamentoIA, StatusJob

logger = logging.getLogger(__name__)

@celery_app.task(name="processar_audio")
def processar_audio_task(job_id: str):
    """
    Simula o Pipeline de Processamento (ASR -> NER -> LLM).
    No ambiente de produção (HPC Mandu), isso chamaria as GPUs.
    """
    logger.info(f"Iniciando processamento do Job ID: {job_id}")
    
    db = SessionLocal()
    try:
        # 1. Recupera o Job
        job = db.query(JobProcessamentoIA).filter(JobProcessamentoIA.id_job == job_id).first()
        if not job:
            logger.error(f"Job {job_id} não encontrado no banco.")
            return False
            
        # 2. Atualiza Status para Processando
        job.status = StatusJob.PROCESSANDO
        db.commit()
        
        # 3. Simula inferência ASR (Whisper)
        logger.info("Executando ASR (Whisper)...")
        time.sleep(3) # Simula os minutos de VRAM no HPC
        
        # 4. Simula Ancoragem Factológica (LeNER-Br)
        logger.info("Extraindo Entidades (LeNER-Br)...")
        time.sleep(2)
        
        # 5. Simula Síntese Jurídica (vLLM Temperatura 0.0)
        logger.info("Gerando Resumo Jurídico Determinístico (LLM)...")
        time.sleep(4)
        
        # 6. Conclui com sucesso
        job.status = StatusJob.CONCLUIDO
        db.commit()
        logger.info(f"Job {job_id} finalizado com sucesso!")
        
        return True

    except Exception as e:
        logger.error(f"Erro no processamento do Job {job_id}: {str(e)}")
        # Poderíamos marcar StatusJob.ERRO aqui
        if job:
            job.status = StatusJob.ERRO
            db.commit()
        return False
        
    finally:
        db.close()
