"""Soft-delete (descarte) de processos + filtro/meta na listagem."""
import pytest
import uuid
from tests import factories

pytestmark = pytest.mark.integration


def test_descartar_oculta_da_lista_padrao(client, valid_token, test_user, db_session):
    chain = factories.full_chain(db_session)
    did = str(chain["depoimento"].id_depoimento)

    # Aparece por padrão.
    r = client.get("/api/v1/processos/", headers=valid_token)
    assert any(i["id_depoimento"] == did for i in r.json()["items"])

    # Descarta (soft-delete).
    rd = client.put(f"/api/v1/processos/{did}/descartar", headers=valid_token)
    assert rd.status_code == 200
    assert rd.json()["descartado"] is True

    # Some da lista padrão e conta no meta.
    r2 = client.get("/api/v1/processos/", headers=valid_token)
    body = r2.json()
    assert not any(i["id_depoimento"] == did for i in body["items"])
    assert body["descartados"] >= 1

    # Aparece com descartados=apenas.
    r3 = client.get("/api/v1/processos/?descartados=apenas", headers=valid_token)
    assert any(i["id_depoimento"] == did for i in r3.json()["items"])


def test_descartar_id_invalido(client, valid_token, test_user):
    r = client.put("/api/v1/processos/nao-uuid/descartar", headers=valid_token)
    assert r.status_code == 422


def test_descartar_inexistente_404(client, valid_token, test_user):
    r = client.put(f"/api/v1/processos/{uuid.uuid4()}/descartar", headers=valid_token)
    assert r.status_code == 404
