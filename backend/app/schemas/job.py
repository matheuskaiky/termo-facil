from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional
from app.models import StatusJob

class JobCreate(BaseModel):
    id_depoimento: UUID4
    # Para o MVP os modelos são mockados, mas poderiam ser passados na requisição
    id_modelo_asr: UUID4
    id_modelo_llm: UUID4

class JobResponse(BaseModel):
    id_job: UUID4
    id_depoimento: UUID4
    status: StatusJob
    
    class Config:
        from_attributes = True # Permite que o Pydantic leia direto do SQLAlchemy
