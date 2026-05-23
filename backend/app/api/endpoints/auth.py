from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.db import get_db
from app.models import Usuario
from app.schemas.admin import UsuarioSchema
from app.api.deps import get_current_user
from app.core.security import verificar_senha, criar_token

router = APIRouter()


class LoginRequest(BaseModel):
    matricula: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.matricula == body.matricula).first()
    if not user or not user.senha_hash or not verificar_senha(body.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Matrícula ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    permissoes = [p.nome_permissao for p in user.cargo.permissoes] if user.cargo else []
    token = criar_token({
        "sub": str(user.id_usuario),
        "cargo": user.cargo.nome_cargo if user.cargo else None,
        "permissoes": permissoes,
    })
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioSchema)
def get_me(current_user: Usuario = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=List[UsuarioSchema])
def list_sim_users(db: Session = Depends(get_db)):
    return db.query(Usuario).all()
