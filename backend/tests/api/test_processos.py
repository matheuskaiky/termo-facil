import uuid

import pytest

from tests.factories import create_delegacia, create_user, create_depoimento

pytestmark = pytest.mark.integration

VALID_CPF = "11144477735"


def _login(client, matricula):
    resp = client.post("/api/v1/auth/login", json={"matricula": matricula, "senha": "senha_forte"})
    assert resp.status_code == 200, resp.json()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_listar_processos_pagination_shape(client, db_session, valid_token, test_user):
    create_depoimento(db_session, test_user, test_user.delegacia)
    create_depoimento(db_session, test_user, test_user.delegacia)
    response = client.get("/api/v1/processos/?limit=1&offset=0", headers=valid_token)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1


def test_escrivao_only_sees_own_processos(client, db_session):
    deleg = create_delegacia(db_session)
    esc_a = create_user(db_session, deleg, "Escrivão", ["CRIAR_TERMO", "EDITAR_TERMO"], "PA0001")
    esc_b = create_user(db_session, deleg, "Escrivão", ["CRIAR_TERMO"], "PB0001")
    create_depoimento(db_session, esc_a, deleg)
    create_depoimento(db_session, esc_b, deleg)

    headers_a = _login(client, "PA0001")
    body = client.get("/api/v1/processos/", headers=headers_a).json()
    assert body["total"] == 1


def test_criar_processo_requires_permission(client, db_session):
    deleg = create_delegacia(db_session)
    create_user(db_session, deleg, "Sem Criar", ["VER_METRICAS"], "PC0001")
    headers = _login(client, "PC0001")
    payload = {
        "num_procedimento": "IP-NEW-1",
        "data_instauracao": "2026-01-01",
        "cpf_depoente": VALID_CPF,
        "nome_depoente": "Fulano",
        "tipo_depoente": "Testemunha",
    }
    response = client.post("/api/v1/processos/novo", headers=headers, json=payload)
    assert response.status_code == 403


def test_criar_processo_success(client, db_session, valid_token, test_user):
    payload = {
        "num_procedimento": "IP-NEW-2",
        "data_instauracao": "2026-01-01",
        "cpf_depoente": VALID_CPF,
        "nome_depoente": "Fulano de Tal",
        "tipo_depoente": "Testemunha",
    }
    response = client.post("/api/v1/processos/novo", headers=valid_token, json=payload)
    assert response.status_code == 200, response.json()
    assert "id_depoimento" in response.json()
