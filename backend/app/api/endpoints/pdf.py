# backend/app/api/endpoints/pdf.py
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, UUID4
from app.db import get_db
from app.models import TermosFinais
from app.api.deps import RequirePermission
import hashlib
import uuid

# Importing the PDF generation service function
from app.services.pdf_service import gerar_pdf_termo_depoimento

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

@router.get("/{job_id}/pdf")
def download_job_pdf(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Generates and triggers the download of the official PDF document 
    for the completed testimony related to the given Job ID.
    """
    termos_finais = db.query(TermosFinais).filter(TermosFinais.id_job == job_id).first()
    if not termos_finais:
        raise HTTPException(status_code=404, detail="Resultado do processamento não encontrado para este Job.")
    
    try:
        pdf_content = gerar_pdf_termo_depoimento(db, termos_finais.id_depoimento)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar o arquivo PDF: {str(e)}")
        
    filename = f"termo_depoimento_{termos_finais.id_depoimento}.pdf"
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )