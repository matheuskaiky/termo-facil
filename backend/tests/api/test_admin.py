import pytest

def test_listar_usuarios_without_permission(client):
    """Testa que um usuário normal não pode ver usuários (se a rota exigir auth)"""
    # Se a rota estivesse protegida, deveria ser 401 sem token, mas a rota em admin costuma estar.
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 401

def test_listar_usuarios_with_permission(client, valid_token):
    response = client.get("/api/v1/admin/users", headers=valid_token)
    # the test_user has GERENCIAR_USUARIOS permission from conftest
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_reset_password(client, valid_token, test_user):
    response = client.post(f"/api/v1/admin/users/{test_user.id_usuario}/reset-password", headers=valid_token)
    assert response.status_code == 200
    data = response.json()
    assert "temp_password" in data
    # verify user's must_change_password flag
    user_me = client.get("/api/v1/auth/me", headers=valid_token)
    assert user_me.json()["must_change_password"] == True
