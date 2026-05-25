# backend/app/api/endpoints/pdf.py
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, UUID4
from app.db import get_db
from app.models import TermosFinais
from app.api.deps import RequirePermission
from app.services.storage_service import pdf_storage
from app.services.pdf_service import gerar_pdf_termo_depoimento
import hashlib
import uuid

router = APIRouter()

class PDFGeneratePayload(BaseModel):
    id_depoimento: UUID4

@router.post("/gerar", dependencies=[Depends(RequirePermission('GERAR_PDF'))])
def gerar_pdf(payload: PDFGeneratePayload, db: Session = Depends(get_db)):
    """
    Generate the official testimony PDF, upload to storage, and return a presigned URL.
    """
    termos = db.query(TermosFinais).filter(TermosFinais.id_depoimento == payload.id_depoimento).first()
    if not termos:
        raise HTTPException(status_code=404, detail="Termos finais do depoimento não encontrados.")

    try:
        pdf_bytes, sha256_hash = gerar_pdf_termo_depoimento(db, payload.id_depoimento)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar o arquivo PDF: {str(e)}")

    object_name = f"{payload.id_depoimento}/termo.pdf"

    try:
        storage_path = pdf_storage.upload_file(pdf_bytes, object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload do PDF: {str(e)}")

    try:
        presigned_url = pdf_storage.generate_presigned_url(object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar URL de download: {str(e)}")

    termos.hash_pdf = sha256_hash
    termos.storage_path_pdf = storage_path
    db.commit()

    return {
        "status": "success",
        "message": "Termo completo (Resumo + Transcrição Literal Anexa) gerado e assinado com sucesso!",
        "id_depoimento": str(payload.id_depoimento),
        "hash_pdf": sha256_hash,
        "pdf_url": presigned_url
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
        pdf_content, _ = gerar_pdf_termo_depoimento(db, termos_finais.id_depoimento)
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
