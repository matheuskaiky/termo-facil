import uuid

from tests.factories import (
    create_delegacia, create_user, create_depoimento, create_job, create_termos,
)


def _login(client, matricula):
    resp = client.post("/api/v1/auth/login", json={"matricula": matricula, "senha": "senha_forte"})
    assert resp.status_code == 200, resp.json()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_listar_termos_empty(client, valid_token):
    response = client.get("/api/v1/termos", headers=valid_token)
    assert response.status_code == 200
    body = response.json()
    assert body == {"total": 0, "items": []}


def test_get_termo_not_found(client, valid_token):
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/termos/{fake_id}", headers=valid_token)
    assert response.status_code == 404


def test_get_termo_invalid_uuid(client, valid_token):
    response = client.get("/api/v1/termos/not-a-uuid", headers=valid_token)
    assert response.status_code == 422


def test_listar_termos_returns_items_and_pagination(client, db_session, valid_token, test_user):
    """Admin test_user sees all termos; response carries total + items."""
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    job = create_job(db_session, dep)
    create_termos(db_session, dep, job)

    response = client.get("/api/v1/termos?limit=10&offset=0", headers=valid_token)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    item = body["items"][0]
    # TermoResumoResponse must NOT leak NER/ASR raw data (LGPD Art. 46 minimization)
    assert "dicionario_ner" not in item
    assert "segmentos_asr" not in item
    assert item["id_depoimento"] == str(dep.id_depoimento)


def test_get_termo_detail_includes_ner_and_segments(client, db_session, valid_token, test_user):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    job = create_job(db_session, dep)
    create_termos(db_session, dep, job, dicionario_ner={"PESSOAS": ["João da Silva"]})

    response = client.get(f"/api/v1/termos/{dep.id_depoimento}", headers=valid_token)
    assert response.status_code == 200
    body = response.json()
    assert body["dicionario_ner"] == {"PESSOAS": ["João da Silva"]}
    assert isinstance(body["segmentos_asr"], list)


def test_put_termo_persists_human_edit(client, db_session, valid_token, test_user):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    job = create_job(db_session, dep)
    create_termos(db_session, dep, job, txt_editado_humano=None)

    response = client.put(
        f"/api/v1/termos/{dep.id_depoimento}",
        headers=valid_token,
        json={"txt_editado_humano": "Texto revisado e assinado pelo escrivão."},
    )
    assert response.status_code == 200
    assert response.json()["txt_editado_humano"] == "Texto revisado e assinado pelo escrivão."


def test_escrivao_cannot_edit_other_escrivao_termo(client, db_session):
    deleg = create_delegacia(db_session)
    user_b = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "EB0001")
    dep_b = create_depoimento(db_session, user_b, deleg)
    job_b = create_job(db_session, dep_b)
    create_termos(db_session, dep_b, job_b)

    create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"], "EA0001")
    headers_a = _login(client, "EA0001")

    response = client.put(
        f"/api/v1/termos/{dep_b.id_depoimento}",
        headers=headers_a,
        json={"txt_editado_humano": "tentativa indevida"},
    )
    assert response.status_code == 403


def test_reclassify_speakers_text_based(client, db_session, valid_token, test_user):
    """Without an audio sample, reclassification uses text-pattern analysis."""
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    job = create_job(db_session, dep)
    create_termos(db_session, dep, job, segmentos_asr=[
        {"start": 0.0, "end": 3.0, "text": "O senhor poderia dizer onde estava?", "speaker": "Depoente"},
        {"start": 3.0, "end": 9.0, "text": "Eu estava em casa, vi tudo e fui embora.", "speaker": "Inquiridor"},
    ])
    response = client.post(f"/api/v1/termos/{dep.id_depoimento}/reclassify-speakers", headers=valid_token)
    assert response.status_code == 200
    assert isinstance(response.json()["segmentos_asr"], list)


def test_reclassify_speakers_no_segments_returns_400(client, db_session, valid_token, test_user):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    job = create_job(db_session, dep)
    create_termos(db_session, dep, job, segmentos_asr=[])
    response = client.post(f"/api/v1/termos/{dep.id_depoimento}/reclassify-speakers", headers=valid_token)
    assert response.status_code == 400
