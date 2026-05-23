import secrets
import string
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Usuario, Cargo, Permissao
from app.schemas.admin import (
    UsuarioSchema, UsuarioUpdateCargoSchema,
    CargoSchema, CargoCreateSchema, CargoUpdatePermissoesSchema, PermissionSchema
)
from app.api.deps import RequirePermission
from app.core.security import hash_senha

_TEMP_PASSWORD_ALPHABET = string.ascii_letters + string.digits


def _gerar_senha_temporaria(length: int = 12) -> str:
    return "".join(secrets.choice(_TEMP_PASSWORD_ALPHABET) for _ in range(length))


class TempPasswordResponse(BaseModel):
    temp_password: str

# Require 'GERENCIAR_USUARIOS' permission for all routes in this controller
router = APIRouter(dependencies=[Depends(RequirePermission('GERENCIAR_USUARIOS'))])

@router.get("/users", response_model=List[UsuarioSchema])
def list_users(db: Session = Depends(get_db)):
    """
    List all users in the system.
    """
    return db.query(Usuario).all()

@router.put("/users/{user_id}/cargo", response_model=UsuarioSchema)
def update_user_cargo(user_id: str, payload: UsuarioUpdateCargoSchema, db: Session = Depends(get_db)):
    """
    Update the cargo (role) of a user.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de usuário inválido.")
    user = db.query(Usuario).filter(Usuario.id_usuario == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
    cargo = db.query(Cargo).filter(Cargo.id_cargo == payload.id_cargo).first()
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo não encontrado.")

    user.id_cargo = payload.id_cargo
    db.commit()
    db.refresh(user)
    return user

@router.get("/cargos", response_model=List[CargoSchema])
def list_cargos(db: Session = Depends(get_db)):
    """
    List all roles (cargos) and their permissions.
    """
    return db.query(Cargo).all()

@router.post("/cargos", response_model=CargoSchema, status_code=201)
def create_cargo(payload: CargoCreateSchema, db: Session = Depends(get_db)):
    """
    Create a new role (cargo) and associate selected permissions.
    """
    existing_cargo = db.query(Cargo).filter(Cargo.nome_cargo == payload.nome_cargo).first()
    if existing_cargo:
        raise HTTPException(status_code=400, detail="Já existe um cargo com este nome.")
        
    # Retrieve permissions from DB
    permissions = db.query(Permissao).filter(Permissao.id_permissao.in_(payload.permissoes_ids)).all()
    if len(permissions) != len(payload.permissoes_ids):
        raise HTTPException(status_code=400, detail="Alguma das permissões informadas não foi encontrada.")
        
    new_cargo = Cargo(
        nome_cargo=payload.nome_cargo,
        permissoes=permissions
    )
    db.add(new_cargo)
    db.commit()
    db.refresh(new_cargo)
    return new_cargo

@router.get("/permissions", response_model=List[PermissionSchema])
def list_permissions(db: Session = Depends(get_db)):
    return db.query(Permissao).all()


@router.put("/cargos/{cargo_id}/permissions", response_model=CargoSchema)
def update_cargo_permissions(cargo_id: str, payload: CargoUpdatePermissoesSchema, db: Session = Depends(get_db)):
    try:
        cid = uuid.UUID(cargo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de cargo inválido.")
    cargo = db.query(Cargo).filter(Cargo.id_cargo == cid).first()
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo não encontrado.")
    permissions = db.query(Permissao).filter(Permissao.id_permissao.in_(payload.permissoes_ids)).all()
    if len(permissions) != len(payload.permissoes_ids):
        raise HTTPException(status_code=400, detail="Uma ou mais permissões não foram encontradas.")
    cargo.permissoes = permissions
    db.commit()
    db.refresh(cargo)
    return cargo


@router.post("/users/{user_id}/reset-password", response_model=TempPasswordResponse)
def reset_user_password(user_id: str, db: Session = Depends(get_db)):
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de usuário inválido.")
    user = db.query(Usuario).filter(Usuario.id_usuario == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    temp = _gerar_senha_temporaria()
    user.senha_hash = hash_senha(temp)
    user.must_change_password = True
    db.commit()
    # temp_password is returned once and never stored in plaintext
    return TempPasswordResponse(temp_password=temp)
