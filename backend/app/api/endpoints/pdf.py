from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, UUID4
from app.db import get_db
from app.models import TermosFinais
from app.api.deps import RequirePermission
import hashlib

router = APIRouter()

class PDFGeneratePayload(BaseModel):
    id_depoimento: UUID4

@router.post("/gerar", dependencies=[Depends(RequirePermission('GERAR_PDF'))])
def gerar_pdf(payload: PDFGeneratePayload, db: Session = Depends(get_db)):
    """
    Mock endpoint to generate a deposition PDF.
    Updates TermosFinais with a simulated hash_pdf and returns it.
    """
    termos = db.query(TermosFinais).filter(TermosFinais.id_depoimento == payload.id_depoimento).first()
    if not termos:
        raise HTTPException(status_code=404, detail="Termos finais do depoimento não encontrados.")
    
    # Mock PDF generation by hashing the edited or original transcript
    content_to_hash = termos.txt_editado_humano or termos.txt_original_ia or "Empty"
    mock_hash = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()
    
    termos.hash_pdf = mock_hash
    db.commit()
    
    return {
        "status": "success",
        "message": "PDF gerado e assinado digitalmente com sucesso!",
        "id_depoimento": str(payload.id_depoimento),
        "hash_pdf": mock_hash
    }
