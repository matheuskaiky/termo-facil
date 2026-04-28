import time
import logging
from app.core.celery_app import celery_app
from app.db import SessionLocal
from app.models import JobProcessamentoIA, StatusJob, TermosFinais
import hashlib

logger = logging.getLogger(__name__)

mock_asr = (
    "[00:02] INQUIRIDOR: Qual o seu nome completo e onde você estava ontem às 22h?\n"
    "[00:08] DEPOENTE: Meu nome é Carlos Eduardo Alves. Eu estava na praça central "
    "quando vi dois homens numa moto preta passarem muito rápido. A placa parecia ser ABC-1234.\n"
    "[00:15] INQUIRIDOR: Você notou alguma característica física ou armada?\n"
    "[00:21] DEPOENTE: O garupa tava com uma jaqueta vermelha e parecia segurar uma arma preta."
)
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
    Simulates the Processing Pipeline (ASR -> NER -> LLM).
    In production (HPC Mandu), this would call the local GPUs.
    """
    logger.info(f"Iniciando processamento do Job ID: {job_id}")
    
    db = SessionLocal()
    try:
        # 1. Fetch the Job record
        job = db.query(JobProcessamentoIA).filter(JobProcessamentoIA.id_job == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return False
            
        # 2. Update Status to Processando (Processing)
        job.status = StatusJob.PROCESSANDO
        db.commit()
        
        # 3. Simulate ASR inference (Whisper)
        logger.info("Running ASR (Whisper)...")
        time.sleep(3) # Simulates VRAM processing time
        
        # 4. Simulate Fact Anchoring (LeNER-Br)
        logger.info("Extracting Entities (LeNER-Br)...")
        time.sleep(2)
        
        # 5. Simulate Legal Synthesis (vLLM Temperature 0.0)
        logger.info("Generating Deterministic Legal Summary (LLM)...")
        time.sleep(4)
        
        resultado_final = TermosFinais(
            id_depoimento=job.id_depoimento,
            id_job=job.id_job,
            txt_literal_asr=mock_asr,
            txt_original_ia=mock_llm,
            dicionario_ner=mock_ner,
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
        # We could set StatusJob.ERRO here
        if job:
            job.status = StatusJob.ERRO
            db.commit()
        return False
        
    finally:
        db.close()
