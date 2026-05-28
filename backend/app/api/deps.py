import uuid
from fastapi import Depends, HTTPException, Request, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Usuario
from app.core.security import verificar_token
from app.core.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)

_CHANGE_PASSWORD_SUFFIX = "/auth/change-password"


def _enforce_password_change(user: Usuario, request: Request) -> Usuario:
    """Block access to all endpoints except change-password when user must reset their password."""
    if user.must_change_password and not request.url.path.endswith(_CHANGE_PASSWORD_SUFFIX):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="password_change_required")
    return user


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    x_user_id: str = Header(None, alias="X-User-Id"),
) -> Usuario:
    # 1. JWT via Authorization: Bearer <token>
    if credentials:
        try:
            payload = verificar_token(credentials.credentials)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
            user = db.query(Usuario).filter(Usuario.id_usuario == uuid.UUID(user_id)).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")
            return _enforce_password_change(user, request)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token JWT inválido ou expirado.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 2. Legacy mock header X-User-Id (dev only — ONLY in development/test, never in staging/prod)
    if x_user_id:
        if settings.APP_ENV not in ("development", "test"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticação via Bearer Token obrigatória.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            user = db.query(Usuario).filter(Usuario.id_usuario == uuid.UUID(x_user_id)).first()
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de ID inválido.")
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")
        return _enforce_password_change(user, request)

    # 3. Dev fallback: first user in DB (ONLY in development/test, never in staging/prod)
    if settings.APP_ENV not in ("development", "test"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação via Bearer Token obrigatória.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(Usuario).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nenhum usuário cadastrado. Execute o seed.",
        )
    return _enforce_password_change(user, request)


class RequirePermission:
    def __init__(self, permission_name: str):
        self.permission_name = permission_name

    def __call__(
        self,
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Usuario:
        if not current_user.cargo:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário sem cargo atribuído.")
        permissions = [p.nome_permissao for p in current_user.cargo.permissoes]
        if self.permission_name not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado: Permissão '{self.permission_name}' é necessária.",
            )
        return current_user
