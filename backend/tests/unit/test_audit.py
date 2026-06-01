"""Unit tests for app.utils.audit.log_access (LGPD Art. 37)."""
import pytest

from app.models import AuditLog
from app.utils.audit import log_access
from tests.factories import create_delegacia, create_user

pytestmark = pytest.mark.integration  # uses the DB session


def test_log_access_persists_entry(db_session):
    deleg = create_delegacia(db_session)
    user = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "LA1")

    log_access("GET /termos/{id}", "recurso-123", db_session, user)

    logs = db_session.query(AuditLog).all()
    assert len(logs) == 1
    assert logs[0].endpoint == "GET /termos/{id}"
    assert logs[0].id_recurso == "recurso-123"
    assert logs[0].id_usuario == user.id_usuario


def test_log_access_never_propagates_failure(db_session, mocker):
    """Audit writes must not break the main request flow."""
    deleg = create_delegacia(db_session)
    user = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "LA2")

    mocker.patch.object(db_session, "commit", side_effect=Exception("db down"))
    # Should swallow the exception internally
    log_access("GET /x", None, db_session, user)
