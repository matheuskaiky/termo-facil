"""Post-signature immutability guard.

Once the official PDF is generated (TermosFinais.hash_pdf is set), the testimony
is signed and legally final — RN-03 — and nothing about it may change anymore.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import TermosFinais


def is_signed(db: Session, id_depoimento) -> bool:
    row = (
        db.query(TermosFinais.hash_pdf)
        .filter(TermosFinais.id_depoimento == id_depoimento)
        .first()
    )
    return bool(row and row[0])


def assert_not_signed(db: Session, id_depoimento) -> None:
    if is_signed(db, id_depoimento):
        raise HTTPException(
            status_code=409,
            detail="Termo já assinado — nenhuma alteração é permitida.",
        )
