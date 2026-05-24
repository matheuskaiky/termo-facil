import pytest

def test_login_success(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"matricula": test_user.matricula, "senha": "senha_forte"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"matricula": test_user.matricula, "senha": "senha_errada"}
    )
    assert response.status_code == 401
    assert "Matrícula ou senha inválidos" in response.json()["detail"]

def test_login_invalid_matricula(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"matricula": "999999", "senha": "senha"}
    )
    assert response.status_code == 401

def test_get_me(client, valid_token, test_user):
    response = client.get(
        "/api/v1/auth/me",
        headers=valid_token
    )
    assert response.status_code == 200
    data = response.json()
    assert data["matricula"] == test_user.matricula
    assert data["nome"] == test_user.nome

def test_change_password(client, valid_token, test_user):
    response = client.post(
        "/api/v1/auth/change-password",
        headers=valid_token,
        json={"nova_senha": "nova_senha_forte123"}
    )
    assert response.status_code == 200
    # verify login with new password works
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"matricula": test_user.matricula, "senha": "nova_senha_forte123"}
    )
    assert login_resp.status_code == 200
