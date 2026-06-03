# Shared pytest fixtures.
# Run: python -m pytest -v --cov=app

import pytest
import os
from unittest.mock import MagicMock
import sys

# Mock boto3 before importing app modules to prevent MinIO connection attempts
sys.modules['boto3'] = MagicMock()
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.client'] = MagicMock()
sys.modules['botocore.config'] = MagicMock()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# 1. Custom SQLAlchemy compilation for SQLite in-memory testing
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID, BYTEA


@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(UUID, 'sqlite')
def compile_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"


@compiles(BYTEA, 'sqlite')
def compile_bytea_sqlite(type_, compiler, **kw):
    return "BLOB"


# 2. Setup SQLite DB
from app.db import Base, get_db
from app.main import app
from app.models import Usuario, Cargo, Permissao, Delegacia
from app.core.security import hash_senha
from app.core.permissions import Permission
import uuid

from sqlalchemy.pool import StaticPool

# slowapi's limiter is a module-level singleton that counts requests per client
# IP across the whole test session. The TestClient always reports the same
# address, so after 10 logins every subsequent test would get HTTP 429.
# Disable it globally for tests; the one test that verifies the limiter
# re-enables it explicitly (see tests/api/test_auth.py).
from app.core.rate_limiter import limiter as _limiter
_limiter.enabled = False

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All permissions — the default test_user is an "everything" user so endpoint
# tests don't each have to wire up RBAC. Ownership/permission denial paths are
# covered by dedicated tests that build scoped users via tests/factories.py.
_ALL_PERMISSIONS = [
    Permission.UPLOAD_AUDIO, Permission.EDITAR_TERMO, Permission.GERAR_PDF,
    Permission.GERENCIAR_USUARIOS, Permission.VER_METRICAS, Permission.CRIAR_TERMO,
    Permission.REDEFINIR_SENHA, Permission.ACESSAR_DEV_DEBUG,
]


@pytest.fixture(scope="function")
def setup_database():
    """Create all tables in the in-memory SQLite database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(setup_database):
    """Provides a fresh database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a TestClient overriding the DB dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Creates a default 'everything' user, cargo and delegacia in the test DB."""
    delegacia = Delegacia(
        id_delegacia=uuid.uuid4(),
        nome_unidade="DELEGACIA DE TESTE",
        cep="64000-000",
        logradouro="Rua de Teste",
        numero="100",
        municipio="Teresina",
        uf="PI",
        ativo=True,
    )
    db_session.add(delegacia)

    cargo = Cargo(id_cargo=uuid.uuid4(), nome_cargo="Administrador Teste")
    perms = [
        Permissao(id_permissao=uuid.uuid4(), nome_permissao=nome, descricao_permissao=f"Permite {nome}")
        for nome in _ALL_PERMISSIONS
    ]
    cargo.permissoes.extend(perms)
    db_session.add(cargo)
    db_session.add_all(perms)

    user = Usuario(
        id_usuario=uuid.uuid4(),
        id_delegacia=delegacia.id_delegacia,
        id_cargo=cargo.id_cargo,
        matricula="123456",
        nome="Usuario de Teste",
        senha_hash=hash_senha("senha_forte"),
        must_change_password=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def valid_token(client, test_user):
    """Authenticates the test_user and returns the Bearer token header."""
    response = client.post(
        "/api/v1/auth/login",
        json={"matricula": "123456", "senha": "senha_forte"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def mock_celery(mocker):
    """Mocks celery send_task so we don't start real background jobs."""
    return mocker.patch("app.core.celery_app.celery_app.send_task", return_value=True)


@pytest.fixture(scope="function")
def mock_storage(mocker):
    """Mocks all MinIO storage calls (audio, pdf, speaker samples)."""
    mocker.patch("app.services.storage_service.audio_storage.upload_file", return_value="s3://test/audio.wav")
    mocker.patch("app.services.storage_service.audio_storage.generate_presigned_url", return_value="http://localhost:9000/audio.wav")
    mocker.patch("app.services.storage_service.audio_storage.delete_file", return_value=None)
    mocker.patch("app.services.storage_service.pdf_storage.upload_file", return_value="termos-finais/file.pdf")
    mocker.patch("app.services.storage_service.pdf_storage.generate_presigned_url", return_value="http://localhost:9000/termos-finais/file.pdf")
    mocker.patch("app.services.storage_service.speaker_samples_storage.upload_file", return_value="speaker-samples/sample.wav")
