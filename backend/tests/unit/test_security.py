"""Unit tests for app.core.security — bcrypt hashing and JWT handling."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt, JWTError

from app.core import security
from app.core.config import settings

pytestmark = pytest.mark.unit


def test_hash_senha_is_not_plaintext_and_verifies():
    hashed = security.hash_senha("senha_forte")
    assert hashed != "senha_forte"
    assert security.verificar_senha("senha_forte", hashed) is True


def test_verificar_senha_wrong_password():
    hashed = security.hash_senha("senha_forte")
    assert security.verificar_senha("errada", hashed) is False


def test_verificar_senha_none_hash_runs_dummy_and_returns_false():
    """When the user doesn't exist (hash None), bcrypt still runs (timing-attack
    prevention) and the result is always False."""
    assert security.verificar_senha("qualquer", None) is False


def test_criar_e_verificar_token_roundtrip():
    user_id = str(uuid.uuid4())
    token = security.criar_token({"sub": user_id, "cargo": "Escrivão"})
    payload = security.verificar_token(token)
    assert payload["sub"] == user_id
    assert payload["cargo"] == "Escrivão"
    assert "exp" in payload


def test_verificar_token_tampered_raises():
    token = security.criar_token({"sub": "x"})
    with pytest.raises(JWTError):
        security.verificar_token(token + "tampered")


def test_verificar_token_expired_raises():
    payload = {"sub": "x", "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
    expired = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=security.ALGORITHM)
    with pytest.raises(JWTError):
        security.verificar_token(expired)


def test_verificar_token_wrong_secret_raises():
    payload = {"sub": "x", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    forged = jwt.encode(payload, "chave-errada", algorithm=security.ALGORITHM)
    with pytest.raises(JWTError):
        security.verificar_token(forged)
