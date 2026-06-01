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


def test_metricas_requires_ver_metricas_permission(client, db_session):
    deleg = create_delegacia(db_session)
    create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "MX0001")
    headers = _login(client, "MX0001")
    response = client.get("/api/v1/metricas", headers=headers)
    assert response.status_code == 403


def test_metricas_aggregations(client, db_session, valid_token, test_user):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    job = create_job(db_session, dep, status=StatusJob.CONCLUIDO)
    create_termos(db_session, dep, job)

    response = client.get("/api/v1/metricas", headers=valid_token)
    assert response.status_code == 200
    data = response.json()
    assert data["total_depoimentos"] == 1
    assert data["total_termos_gerados"] == 1
    assert "jobs_por_status" in data
    assert data["jobs_por_status"]["Concluído"] == 1
    assert data["taxa_sucesso_pct"] == 100.0
    # horas economizadas só conta PDFs exportados (hash_pdf preenchido) → 0 aqui
    assert data["horas_economizadas_estimadas"] == 0.0


def test_metricas_empty_system(client, valid_token, test_user):
    response = client.get("/api/v1/metricas", headers=valid_token)
    assert response.status_code == 200
    data = response.json()
    assert data["total_depoimentos"] == 0
    assert data["taxa_sucesso_pct"] == 0.0
