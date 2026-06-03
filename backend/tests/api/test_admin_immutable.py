"""
PARTE 3 — o cargo Admin é imutável e onipotente:
- onipotente: passa em qualquer RequirePermission e /auth/me lista todas as permissões,
  mesmo que o cargo Admin não tenha permissões atreladas no banco;
- imutável: nenhuma alteração ao cargo Admin é aceita (nem por um Admin) → HTTP 403.
"""
import pytest

from tests.factories import create_delegacia, create_user, get_or_create_cargo, DEFAULT_PASSWORD
from app.models import Cargo

pytestmark = pytest.mark.integration


def _login(client, matricula: str) -> dict:
    r = client.post("/api/v1/auth/login", json={"matricula": matricula, "senha": DEFAULT_PASSWORD})
    assert r.status_code == 200, r.json()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _admin_token(client, db_session):
    deleg = create_delegacia(db_session)
    # Garante que existam permissões no banco (para checar a onipotência no /me),
    # mas o cargo Admin é criado SEM nenhuma permissão atrelada.
    get_or_create_cargo(db_session, "Escrivão", ["EDITAR_TERMO", "GERAR_PDF"])
    admin = create_user(db_session, deleg, "Admin", [], matricula="ADMIN1")
    return _login(client, "ADMIN1"), admin


def test_admin_e_onipotente_em_rota_protegida(client, db_session):
    """GET /admin/users exige GERENCIAR_USUARIOS; o Admin passa mesmo sem ter a permissão."""
    token, _ = _admin_token(client, db_session)
    r = client.get("/api/v1/admin/users", headers=token)
    assert r.status_code == 200


def test_me_lista_todas_as_permissoes_para_admin(client, db_session):
    token, _ = _admin_token(client, db_session)
    r = client.get("/api/v1/auth/me", headers=token)
    assert r.status_code == 200
    nomes = {p["nome_permissao"] for p in r.json()["cargo"]["permissoes"]}
    # Todas as permissões existentes no banco devem aparecer (EDITAR_TERMO/GERAR_PDF criadas acima).
    assert {"EDITAR_TERMO", "GERAR_PDF"}.issubset(nomes)


def test_cargo_admin_imutavel_para_admin(client, db_session):
    """Nem o próprio Admin pode alterar as permissões do cargo Admin."""
    token, _ = _admin_token(client, db_session)
    admin_cargo = db_session.query(Cargo).filter(Cargo.nome_cargo == "Admin").first()
    r = client.put(
        f"/api/v1/admin/cargos/{admin_cargo.id_cargo}/permissions",
        headers=token,
        json={"permissoes_ids": []},
    )
    assert r.status_code == 403


def test_cargo_admin_imutavel_para_gerente(client, db_session, valid_token, test_user):
    """Um usuário com GERENCIAR_USUARIOS também não consegue alterar o cargo Admin."""
    admin_cargo = get_or_create_cargo(db_session, "Admin", [])
    r = client.put(
        f"/api/v1/admin/cargos/{admin_cargo.id_cargo}/permissions",
        headers=valid_token,
        json={"permissoes_ids": []},
    )
    assert r.status_code == 403
