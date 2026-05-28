import logging
from sqlalchemy.orm import Session
from app.models import AuditLog, Usuario

logger = logging.getLogger(__name__)


def log_access(endpoint: str, id_recurso: str | None, db: Session, user: Usuario) -> None:
    """
    Records a personal data access event for LGPD Art. 37 compliance.
    Failures are logged but never propagate — audit must not break the main flow.
    """
    try:
        db.add(AuditLog(
            id_usuario=user.id_usuario,
            endpoint=endpoint,
            id_recurso=str(id_recurso) if id_recurso else None,
        ))
        db.commit()
    except Exception:
        logger.exception("Failed to write audit log entry (endpoint=%s, recurso=%s)", endpoint, id_recurso)
        db.rollback()
