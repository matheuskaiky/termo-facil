"""RN-03: depois de assinado (hash_pdf setado), nada pode mudar."""
import pytest
from tests import factories

pytestmark = pytest.mark.integration

WAV = b"RIFF\x24\x08\x00\x00WAVEfmt "


def _sign(db, termos):
    termos.hash_pdf = "a" * 64
    db.commit()


def test_edicao_bloqueada_apos_assinado(client, valid_token, test_user, db_session):
    chain = factories.full_chain(db_session)
    _sign(db_session, chain["termos"])
    did = str(chain["depoimento"].id_depoimento)
    r = client.put(f"/api/v1/termos/{did}", json={"txt_editado_humano": "novo"}, headers=valid_token)
    assert r.status_code == 409


def test_speakers_bloqueado_apos_assinado(client, valid_token, test_user, db_session):
    chain = factories.full_chain(db_session)
    _sign(db_session, chain["termos"])
    did = str(chain["depoimento"].id_depoimento)
    r = client.post(f"/api/v1/termos/{did}/speakers",
                    json={"mapping": {"Inquiridor": {"role": "Depoente"}}}, headers=valid_token)
    assert r.status_code == 409


def test_descartar_bloqueado_apos_assinado(client, valid_token, test_user, db_session):
    chain = factories.full_chain(db_session)
    _sign(db_session, chain["termos"])
    did = str(chain["depoimento"].id_depoimento)
    r = client.put(f"/api/v1/processos/{did}/descartar", headers=valid_token)
    assert r.status_code == 409


def test_upload_bloqueado_apos_assinado(client, valid_token, test_user, db_session, mock_storage, mock_celery):
    chain = factories.full_chain(db_session)
    _sign(db_session, chain["termos"])
    did = str(chain["depoimento"].id_depoimento)
    files = {"file": ("a.wav", WAV, "audio/wav")}
    r = client.post("/api/v1/upload/audio", headers=valid_token, files=files, data={"id_depoimento": did})
    assert r.status_code == 409


def test_reprocessar_bloqueado_apos_assinado(client, valid_token, test_user, db_session):
    chain = factories.full_chain(db_session)
    _sign(db_session, chain["termos"])
    jid = str(chain["job"].id_job)
    r = client.post(f"/api/v1/jobs/{jid}/reprocessar", headers=valid_token)
    assert r.status_code == 409
