import uuid

import pytest

from app.models import TermosFinais, MidiaBruta
from tests.factories import (
    create_delegacia, create_user, create_depoimento, create_job, create_termos, create_midia,
)

pytestmark = pytest.mark.integration


def _login(client, matricula):
    resp = client.post("/api/v1/auth/login", json={"matricula": matricula, "senha": "senha_forte"})
    assert resp.status_code == 200, resp.json()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_gerar_pdf_success_and_lgpd_purge(client, db_session, valid_token, test_user, mock_storage):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    create_midia(db_session, dep)
    job = create_job(db_session, dep)
    create_termos(
        db_session, dep, job,
        dicionario_ner={"PESSOAS": ["João da Silva"]},
        segmentos_asr=[{"start": 0, "end": 3, "text": "Pergunta.", "speaker": "Inquiridor"}],
    )

    response = client.post("/api/v1/pdf/gerar", headers=valid_token, json={"id_depoimento": str(dep.id_depoimento)})
    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["status"] == "success"
    assert len(body["hash_pdf"]) == 64
    assert body["pdf_url"].startswith("http")

    # RN-04 (LGPD): NER dict and ASR segments must be purged after export
    db_session.expire_all()
    termo = db_session.query(TermosFinais).filter_by(id_depoimento=dep.id_depoimento).first()
    assert termo.dicionario_ner is None
    assert termo.segmentos_asr is None
    assert termo.hash_pdf is not None
    assert termo.data_exportacao_pdf is not None


def test_gerar_pdf_termos_not_found(client, valid_token, test_user):
    response = client.post("/api/v1/pdf/gerar", headers=valid_token, json={"id_depoimento": str(uuid.uuid4())})
    assert response.status_code == 404


def test_gerar_pdf_requires_permission(client, db_session):
    deleg = create_delegacia(db_session)
    create_user(db_session, deleg, "Sem PDF", ["EDITAR_TERMO"], "PG0001")
    headers = _login(client, "PG0001")
    response = client.post("/api/v1/pdf/gerar", headers=headers, json={"id_depoimento": str(uuid.uuid4())})
    assert response.status_code == 403


def test_download_pdf_requires_auth(client):
    response = client.get(f"/api/v1/pdf/{uuid.uuid4()}/pdf")
    assert response.status_code == 401


def test_download_pdf_returns_pdf_bytes(client, db_session, valid_token, test_user):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    job = create_job(db_session, dep)
    create_termos(db_session, dep, job)
    response = client.get(f"/api/v1/pdf/{job.id_job}/pdf", headers=valid_token)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
