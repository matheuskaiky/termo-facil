import uuid

from tests.factories import create_user, get_or_create_cargo
from app.models import Cargo, Permissao


def test_listar_usuarios_without_auth(client):
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 401


def test_listar_usuarios_with_permission(client, valid_token):
    response = client.get("/api/v1/admin/users", headers=valid_token)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data and "items" in data
    assert isinstance(data["items"], list)


def test_list_permissions(client, valid_token, test_user):
    response = client.get("/api/v1/admin/permissions", headers=valid_token)
    assert response.status_code == 200
    nomes = {p["nome_permissao"] for p in response.json()}
    assert "GERENCIAR_USUARIOS" in nomes


def test_list_cargos(client, valid_token, test_user):
    response = client.get("/api/v1/admin/cargos", headers=valid_token)
    assert response.status_code == 200
    assert any(c["nome_cargo"] == "Administrador Teste" for c in response.json())


def test_create_cargo(client, db_session, valid_token, test_user):
    perm = db_session.query(Permissao).filter(Permissao.nome_permissao == "VER_METRICAS").first()
    response = client.post(
        "/api/v1/admin/cargos",
        headers=valid_token,
        json={"nome_cargo": "Gestor Estratégico", "permissoes_ids": [str(perm.id_permissao)]},
    )
    assert response.status_code == 201, response.json()
    assert response.json()["nome_cargo"] == "Gestor Estratégico"


def test_create_cargo_duplicate_name(client, valid_token, test_user):
    response = client.post(
        "/api/v1/admin/cargos",
        headers=valid_token,
        json={"nome_cargo": "Administrador Teste", "permissoes_ids": []},
    )
    assert response.status_code == 400


def test_update_user_cargo(client, db_session, valid_token, test_user):
    target = create_user(db_session, test_user.delegacia, "Escrivão", ["EDITAR_TERMO"], "TG0001")
    novo_cargo = get_or_create_cargo(db_session, "Delegado", ["EDITAR_TERMO"])
    response = client.put(
        f"/api/v1/admin/users/{target.id_usuario}/cargo",
        headers=valid_token,
        json={"id_cargo": str(novo_cargo.id_cargo)},
    )
    assert response.status_code == 200
    assert str(response.json()["cargo"]["id_cargo"]) == str(novo_cargo.id_cargo)


def test_update_own_cargo_forbidden(client, db_session, valid_token, test_user):
    """Self-modification guard (M-7/M-8): a user cannot change their own cargo."""
    other_cargo = get_or_create_cargo(db_session, "Outro Cargo", ["EDITAR_TERMO"])
    response = client.put(
        f"/api/v1/admin/users/{test_user.id_usuario}/cargo",
        headers=valid_token,
        json={"id_cargo": str(other_cargo.id_cargo)},
    )
    assert response.status_code == 400


def test_reset_password(client, db_session, valid_token, test_user):
    """Reset another user's password — returns a one-time temp password and sets the flag."""
    target = create_user(db_session, test_user.delegacia, "Escrivão", ["EDITAR_TERMO"], "RP0001")
    response = client.post(f"/api/v1/admin/users/{target.id_usuario}/reset-password", headers=valid_token)
    assert response.status_code == 200
    assert "temp_password" in response.json()

    db_session.expire_all()
    refreshed = db_session.query(type(target)).filter_by(id_usuario=target.id_usuario).first()
    assert refreshed.must_change_password is True


def test_reset_own_password_forbidden(client, valid_token, test_user):
    response = client.post(f"/api/v1/admin/users/{test_user.id_usuario}/reset-password", headers=valid_token)
    assert response.status_code == 400
