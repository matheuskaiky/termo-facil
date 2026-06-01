import uuid

import pytest

from app.models import StatusJob
from tests.factories import (
    create_delegacia, create_user, create_depoimento, create_job, create_termos,
)

pytestmark = pytest.mark.integration


def _login(client, matricula):
    resp = client.post("/api/v1/auth/login", json={"matricula": matricula, "senha": "senha_forte"})
    assert resp.status_code == 200, resp.json()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_get_job_status(client, db_session, valid_token, test_user):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    job = create_job(db_session, dep, status=StatusJob.TRANSCREVENDO)
    response = client.get(f"/api/v1/jobs/{job.id_job}", headers=valid_token)
    assert response.status_code == 200
    assert response.json()["status"] == "Transcrevendo"


def test_get_job_not_found(client, valid_token, test_user):
    response = client.get(f"/api/v1/jobs/{uuid.uuid4()}", headers=valid_token)
    assert response.status_code == 404


def test_get_job_requires_editar_termo_permission(client, db_session):
    deleg = create_delegacia(db_session)
    create_user(db_session, deleg, "Sem Permissao", ["VER_METRICAS"], "NP0001")
    headers = _login(client, "NP0001")
    response = client.get(f"/api/v1/jobs/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 403


def test_escrivao_cannot_read_other_escrivao_job(client, db_session):
    deleg = create_delegacia(db_session)
    esc_b = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "JB0001")
    dep_b = create_depoimento(db_session, esc_b, deleg)
    job_b = create_job(db_session, dep_b)

    create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "JA0001")
    headers_a = _login(client, "JA0001")
    response = client.get(f"/api/v1/jobs/{job_b.id_job}", headers=headers_a)
    assert response.status_code == 403


def test_get_job_result(client, db_session, valid_token, test_user):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    job = create_job(db_session, dep)
    create_termos(db_session, dep, job, txt_original_ia="Resumo final.")
    response = client.get(f"/api/v1/jobs/{job.id_job}/resultado", headers=valid_token)
    assert response.status_code == 200
    assert response.json()["txt_original_ia"] == "Resumo final."


def test_get_job_result_not_found(client, valid_token, test_user):
    response = client.get(f"/api/v1/jobs/{uuid.uuid4()}/resultado", headers=valid_token)
    assert response.status_code == 404
