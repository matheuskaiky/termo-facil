import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-inseguro-troque-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    return _pwd_context.hash(senha)


def verificar_senha(senha_plain: str, senha_hash: str) -> bool:
    return _pwd_context.verify(senha_plain, senha_hash)


def criar_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str) -> dict:
    """Raises JWTError if token is invalid or expired."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
