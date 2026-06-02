"""Admin user endpoints: get, history, status, create, update, check-matricula."""
import pytest
import uuid
from tests import factories

pytestmark = pytest.mark.integration


def _deleg_cargo(db):
    deleg = factories.create_delegacia(db, nome="DEL USERS")
    cargo = factories.get_or_create_cargo(db, "Escrivão", ["EDITAR_TERMO"])
    return deleg, cargo


def test_create_get_update_user(client, valid_token, test_user, db_session):
    deleg, cargo = _deleg_cargo(db_session)
    payload = {
        "matricula": "NEW123",
        "nome": "novo servidor",
        "id_delegacia": str(deleg.id_delegacia),
        "id_cargo": str(cargo.id_cargo),
    }
    r = client.post("/api/v1/admin/users", json=payload, headers=valid_token)
    assert r.status_code == 201, r.text
    assert r.json()["temp_password"]
    uid = r.json()["id_usuario"]

    g = client.get(f"/api/v1/admin/users/{uid}", headers=valid_token)
    assert g.status_code == 200 and g.json()["nome"] == "novo servidor"
    assert g.json()["ativo"] is True

    u = client.put(f"/api/v1/admin/users/{uid}", json={"nome": "editado"}, headers=valid_token)
    assert u.status_code == 200 and u.json()["nome"] == "editado"


def test_create_user_duplicate_matricula(client, valid_token, test_user, db_session):
    deleg, cargo = _deleg_cargo(db_session)
    payload = {"matricula": "DUP9", "nome": "a", "id_delegacia": str(deleg.id_delegacia), "id_cargo": str(cargo.id_cargo)}
    assert client.post("/api/v1/admin/users", json=payload, headers=valid_token).status_code == 201
    assert client.post("/api/v1/admin/users", json=payload, headers=valid_token).status_code == 400


def test_check_matricula(client, valid_token, test_user, db_session):
    deleg, cargo = _deleg_cargo(db_session)
    client.post("/api/v1/admin/users", json={
        "matricula": "CHK1", "nome": "x", "id_delegacia": str(deleg.id_delegacia), "id_cargo": str(cargo.id_cargo)
    }, headers=valid_token)
    taken = client.get("/api/v1/admin/users/check-matricula?matricula=CHK1", headers=valid_token)
    assert taken.json()["available"] is False
    free = client.get("/api/v1/admin/users/check-matricula?matricula=LIVRE999", headers=valid_token)
    assert free.json()["available"] is True


def test_user_history_is_list(client, valid_token, test_user):
    r = client.get(f"/api/v1/admin/users/{test_user.id_usuario}/history", headers=valid_token)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_status_toggle_other_user(client, valid_token, test_user, db_session):
    deleg, cargo = _deleg_cargo(db_session)
    uid = client.post("/api/v1/admin/users", json={
        "matricula": "ST1", "nome": "x", "id_delegacia": str(deleg.id_delegacia), "id_cargo": str(cargo.id_cargo)
    }, headers=valid_token).json()["id_usuario"]
    r = client.put(f"/api/v1/admin/users/{uid}/status", json={"ativo": False}, headers=valid_token)
    assert r.status_code == 200 and r.json()["ativo"] is False


def test_status_cannot_change_self(client, valid_token, test_user):
    r = client.put(f"/api/v1/admin/users/{test_user.id_usuario}/status", json={"ativo": False}, headers=valid_token)
    assert r.status_code == 400


def test_get_unknown_user_404(client, valid_token, test_user):
    r = client.get(f"/api/v1/admin/users/{uuid.uuid4()}", headers=valid_token)
    assert r.status_code == 404
