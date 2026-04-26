from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "termo_facil_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    # Descobre automaticamente os arquivos de tasks:
    imports=["app.tasks.process_audio"]
)
