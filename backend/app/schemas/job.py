
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional
from app.models import StatusJob

class JobCreate(BaseModel):
    id_depoimento: UUID4
    # In the MVP, models are mocked, but they could be requested via the payload
    id_modelo_asr: UUID4
    id_modelo_llm: UUID4

class JobResponse(BaseModel):
    id_job: UUID4
    id_depoimento: UUID4
    status: StatusJob
    
    class Config:
        from_attributes = True # Allows Pydantic to read directly from SQLAlchemy models

class JobResultResponse(BaseModel):
    id_job: UUID4
    id_depoimento: UUID4

    txt_original_ia: Optional[str] = None
    txt_editado_humano: Optional[str] = None
    txt_literal_asr: Optional[str] = None

    class Config:
        from_attributes = True