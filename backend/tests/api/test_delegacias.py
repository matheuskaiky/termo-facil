"""Endpoints de Delegacia (/api/v1/admin/delegacias).

Cobre as regras de negócio novas: nome sempre em MAIÚSCULAS, endereço
obrigatório (CEP/logradouro/numero/municipio/uf), CEP normalizado, IBGE
persistido, e o ciclo CRUD + desativar.
"""

import pytest

pytestmark = pytest.mark.integration

VALID = {
    "nome_unidade": "1ª delegacia de polícia de teresina",
    "sigla": "1ª dp",
    "cep": "64000000",
    "logradouro": "Avenida Frei Serafim",
    "numero": "1500",
    "complemento": "Sala 2",
    "bairro": "Centro",
    "municipio": "Teresina",
    "uf": "pi",
    "cod_ibge": "2211001",
}


def test_create_delegacia_uppercases_name_and_formats_cep(client, valid_token, test_user):
    res = client.post("/api/v1/admin/delegacias", json=VALID, headers=valid_token)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["nome_unidade"] == "1ª DELEGACIA DE POLÍCIA DE TERESINA"
    assert body["cep"] == "64000-000"        # normalizado
    assert body["sigla"] == "1ª DP"          # sigla também em maiúsculas
    assert body["uf"] == "PI"                # uppercased
    assert body["cod_ibge"] == "2211001"     # IBGE persistido
    assert body["ativo"] is True


def test_create_requires_address(client, valid_token, test_user):
    payload = {"nome_unidade": "DELEGACIA SEM ENDEREÇO"}
    res = client.post("/api/v1/admin/delegacias", json=payload, headers=valid_token)
    assert res.status_code == 422  # cep/logradouro/numero/municipio/uf faltando


def test_create_rejects_bad_cep(client, valid_token, test_user):
    payload = {**VALID, "cep": "123"}
    res = client.post("/api/v1/admin/delegacias", json=payload, headers=valid_token)
    assert res.status_code == 422


def test_list_and_get_with_servidores_count(client, valid_token, test_user):
    created = client.post("/api/v1/admin/delegacias", json=VALID, headers=valid_token).json()
    did = created["id_delegacia"]

    lst = client.get("/api/v1/admin/delegacias", headers=valid_token)
    assert lst.status_code == 200
    assert any(d["id_delegacia"] == did for d in lst.json())

    detail = client.get(f"/api/v1/admin/delegacias/{did}", headers=valid_token)
    assert detail.status_code == 200
    assert "servidores_count" in detail.json()


def test_update_delegacia_partial(client, valid_token, test_user):
    did = client.post("/api/v1/admin/delegacias", json=VALID, headers=valid_token).json()["id_delegacia"]
    res = client.put(
        f"/api/v1/admin/delegacias/{did}",
        json={"numero": "999", "nome_unidade": "novo nome"},
        headers=valid_token,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["numero"] == "999"
    assert body["nome_unidade"] == "NOVO NOME"  # uppercase no update também


def test_desativar_delegacia(client, valid_token, test_user):
    did = client.post("/api/v1/admin/delegacias", json=VALID, headers=valid_token).json()["id_delegacia"]
    res = client.put(f"/api/v1/admin/delegacias/{did}/desativar", json={}, headers=valid_token)
    assert res.status_code == 200
    assert res.json()["ativo"] is False


def test_get_unknown_delegacia_404(client, valid_token, test_user):
    import uuid
    res = client.get(f"/api/v1/admin/delegacias/{uuid.uuid4()}", headers=valid_token)
    assert res.status_code == 404
