import os
import bcrypt
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt  # noqa: F401 — re-exported for callers

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-inseguro-troque-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# Generated once at startup for timing-attack prevention (OWASP A07).
# Never matches any real password; only purpose is to spend ~100ms on bcrypt
# when the queried user doesn't exist, so response time leaks no information.
_DUMMY_HASH: bytes = bcrypt.hashpw(b"__dummy__", bcrypt.gensalt())


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha_plain: str, senha_hash: str | None) -> bool:
    """Always runs bcrypt to prevent timing attacks when hash is None."""
    hash_bytes = senha_hash.encode() if senha_hash else _DUMMY_HASH
    result = bcrypt.checkpw(senha_plain.encode(), hash_bytes)
    return result and senha_hash is not None


def criar_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str) -> dict:
    """Raises JWTError if token is invalid or expired."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
