from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator

from app.db import get_db
from app.models import Usuario
from app.schemas.admin import UsuarioSchema
from app.api.deps import get_current_user
from app.core.security import verificar_senha, hash_senha, criar_token
from app.core.rate_limiter import limiter

router = APIRouter()


class LoginRequest(BaseModel):
    matricula: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.matricula == body.matricula).first()
    # verificar_senha always runs bcrypt (even when user is None) to prevent timing attacks
    if not verificar_senha(body.senha, user.senha_hash if user else None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Matrícula ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # An inactive user is blocked from authenticating.
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Contate o administrador.",
        )

    permissoes = [p.nome_permissao for p in user.cargo.permissoes] if user.cargo else []
    token = criar_token({
        "sub": str(user.id_usuario),
        "cargo": user.cargo.nome_cargo if user.cargo else None,
        "permissoes": permissoes,
        "must_change_password": user.must_change_password,
    })
    return TokenResponse(access_token=token)


class ChangePasswordRequest(BaseModel):
    nova_senha: str

    @field_validator("nova_senha")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        return v


@router.post("/change-password", response_model=TokenResponse)
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    current_user.senha_hash = hash_senha(body.nova_senha)
    current_user.must_change_password = False
    db.commit()
    db.refresh(current_user)

    permissoes = [p.nome_permissao for p in current_user.cargo.permissoes] if current_user.cargo else []
    token = criar_token({
        "sub": str(current_user.id_usuario),
        "cargo": current_user.cargo.nome_cargo if current_user.cargo else None,
        "permissoes": permissoes,
        "must_change_password": False,
    })
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioSchema)
def get_me(current_user: Usuario = Depends(get_current_user)):
    return current_user
