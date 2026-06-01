"""Unit tests for apply_depoimento_scope — row-level RBAC filtering."""
import pytest

from app.models import Depoimento
from app.utils.query_scopes import apply_depoimento_scope
from tests.factories import create_delegacia, create_user, create_depoimento

pytestmark = pytest.mark.integration  # uses the DB session


def _scoped_ids(db, user):
    query = apply_depoimento_scope(db.query(Depoimento), user)
    return {str(d.id_depoimento) for d in query.all()}


def test_escrivao_sees_only_own_depoimentos(db_session):
    deleg = create_delegacia(db_session)
    esc_a = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "EA1")
    esc_b = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "EB1")
    dep_a = create_depoimento(db_session, esc_a, deleg)
    create_depoimento(db_session, esc_b, deleg)

    assert _scoped_ids(db_session, esc_a) == {str(dep_a.id_depoimento)}


def test_delegado_sees_whole_delegacia(db_session):
    deleg1 = create_delegacia(db_session, "Del 1")
    deleg2 = create_delegacia(db_session, "Del 2")
    esc1 = create_user(db_session, deleg1, "Escrivão", ["EDITAR_TERMO"], "E1")
    delegado = create_user(db_session, deleg1, "Delegado", ["EDITAR_TERMO"], "D1")
    esc2 = create_user(db_session, deleg2, "Escrivão", ["EDITAR_TERMO"], "E2")

    dep1 = create_depoimento(db_session, esc1, deleg1)
    create_depoimento(db_session, esc2, deleg2)

    assert _scoped_ids(db_session, delegado) == {str(dep1.id_depoimento)}


def test_admin_sees_everything(db_session):
    deleg = create_delegacia(db_session)
    esc = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "EX1")
    admin = create_user(db_session, deleg, "Administrador", ["GERENCIAR_USUARIOS"], "AD1")
    dep = create_depoimento(db_session, esc, deleg)

    assert str(dep.id_depoimento) in _scoped_ids(db_session, admin)
