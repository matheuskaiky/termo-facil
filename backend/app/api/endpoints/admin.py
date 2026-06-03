import secrets
import string
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Usuario, Cargo, Permissao, Delegacia, AuditLog
from app.schemas.admin import (
    UsuarioSchema, UsuarioUpdateCargoSchema, UsuarioStatusSchema,
    UsuarioCreateSchema, UsuarioUpdateSchema, TempPasswordUserResponse,
    CargoSchema, CargoCreateSchema, CargoUpdatePermissoesSchema, PermissionSchema,
    DelegaciaSchema, DelegaciaCreateSchema, DelegaciaUpdateSchema
)
from app.api.deps import RequirePermission, get_current_user
from app.core.permissions import Permission
from app.core.security import hash_senha

_TEMP_PASSWORD_ALPHABET = string.ascii_letters + string.digits


def _gerar_senha_temporaria(length: int = 12) -> str:
    return "".join(secrets.choice(_TEMP_PASSWORD_ALPHABET) for _ in range(length))


class TempPasswordResponse(BaseModel):
    temp_password: str

# Require 'GERENCIAR_USUARIOS' for all general admin routes
router = APIRouter(dependencies=[Depends(RequirePermission(Permission.GERENCIAR_USUARIOS))])

# Separate router: password reset requires REDEFINIR_SENHA (not GERENCIAR_USUARIOS)
reset_router = APIRouter(dependencies=[Depends(RequirePermission(Permission.REDEFINIR_SENHA))])

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
):
    """
    List all users in the system with pagination.
    """
    total = db.query(Usuario).count()
    items = db.query(Usuario).offset(offset).limit(limit).all()
    return {"total": total, "items": [UsuarioSchema.model_validate(u) for u in items]}


def _get_user_or_404(db: Session, user_id: str) -> Usuario:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de usuário inválido.")
    user = db.query(Usuario).filter(Usuario.id_usuario == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


# Static path: must be declared BEFORE "/users/{user_id}" so it isn't shadowed.
@router.get("/users/check-matricula")
def check_matricula(matricula: str, db: Session = Depends(get_db)):
    taken = db.query(Usuario).filter(Usuario.matricula == matricula.strip()).first()
    return {"available": taken is None, "nome": taken.nome if taken else None}


@router.post("/users", response_model=TempPasswordUserResponse, status_code=201)
def create_user(payload: UsuarioCreateSchema, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.matricula == payload.matricula.strip()).first():
        raise HTTPException(status_code=400, detail="Matrícula já cadastrada.")
    if not db.query(Delegacia).filter(Delegacia.id_delegacia == payload.id_delegacia).first():
        raise HTTPException(status_code=404, detail="Delegacia não encontrada.")
    if not db.query(Cargo).filter(Cargo.id_cargo == payload.id_cargo).first():
        raise HTTPException(status_code=404, detail="Cargo não encontrado.")

    temp = _gerar_senha_temporaria()
    user = Usuario(
        matricula=payload.matricula.strip(),
        nome=payload.nome.strip(),
        id_delegacia=payload.id_delegacia,
        id_cargo=payload.id_cargo,
        senha_hash=hash_senha(temp),
        must_change_password=True,
        ativo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TempPasswordUserResponse(
        temp_password=temp, id_usuario=user.id_usuario, matricula=user.matricula, nome=user.nome
    )


@router.get("/users/{user_id}", response_model=UsuarioSchema)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Single user (for the edit screen)."""
    return _get_user_or_404(db, user_id)


@router.get("/users/{user_id}/history")
def get_user_history(
    user_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=200),
):
    """
    Recent activity for a user, read from the LGPD audit_log (Art. 37).
    Returns access events (endpoint + resource + timestamp), newest first.
    """
    user = _get_user_or_404(db, user_id)
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.id_usuario == user.id_usuario)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "endpoint": r.endpoint,
            "id_recurso": r.id_recurso,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]


@router.put("/users/{user_id}/status", response_model=UsuarioSchema)
def set_user_status(
    user_id: str,
    payload: UsuarioStatusSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Activate/deactivate a user. An inactive user cannot log in."""
    user = _get_user_or_404(db, user_id)
    if user.id_usuario == current_user.id_usuario:
        raise HTTPException(status_code=400, detail="Você não pode alterar o próprio status.")
    user.ativo = payload.ativo
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UsuarioSchema)
def update_user(
    user_id: str,
    payload: UsuarioUpdateSchema,
    db: Session = Depends(get_db),
):
    """Update a user's editable fields (nome, delegacia, cargo, status)."""
    user = _get_user_or_404(db, user_id)
    data = payload.model_dump(exclude_unset=True)
    if "id_delegacia" in data and data["id_delegacia"] is not None:
        if not db.query(Delegacia).filter(Delegacia.id_delegacia == data["id_delegacia"]).first():
            raise HTTPException(status_code=404, detail="Delegacia não encontrada.")
    if "id_cargo" in data and data["id_cargo"] is not None:
        if not db.query(Cargo).filter(Cargo.id_cargo == data["id_cargo"]).first():
            raise HTTPException(status_code=404, detail="Cargo não encontrado.")
    for field, value in data.items():
        if field == "nome" and value is not None:
            value = value.strip()
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/cargo", response_model=UsuarioSchema)
def update_user_cargo(
    user_id: str,
    payload: UsuarioUpdateCargoSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Update the cargo (role) of a user.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de usuário inválido.")
    if uid == current_user.id_usuario:
        raise HTTPException(status_code=400, detail="Operação não permitida no próprio usuário.")
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


@reset_router.post("/users/{user_id}/reset-password", response_model=TempPasswordResponse)
def reset_user_password(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de usuário inválido.")
    if uid == current_user.id_usuario:
        raise HTTPException(status_code=400, detail="Operação não permitida no próprio usuário.")
    user = db.query(Usuario).filter(Usuario.id_usuario == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    temp = _gerar_senha_temporaria()
    user.senha_hash = hash_senha(temp)
    user.must_change_password = True
    db.commit()
    # temp_password is returned once and never stored in plaintext
    return TempPasswordResponse(temp_password=temp)


# ── Delegacias (CRUD) ─────────────────────────────────────────────────────
def _get_delegacia_or_404(db: Session, delegacia_id: str) -> Delegacia:
    try:
        did = uuid.UUID(delegacia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID de delegacia inválido.")
    d = db.query(Delegacia).filter(Delegacia.id_delegacia == did).first()
    if not d:
        raise HTTPException(status_code=404, detail="Delegacia não encontrada.")
    return d


@router.get("/delegacias", response_model=List[DelegaciaSchema])
def list_delegacias(db: Session = Depends(get_db)):
    delegacias = db.query(Delegacia).order_by(Delegacia.nome_unidade).all()
    counts = dict(
        db.query(Usuario.id_delegacia, func.count(Usuario.id_usuario))
        .group_by(Usuario.id_delegacia)
        .all()
    )
    result = []
    for d in delegacias:
        data = DelegaciaSchema.model_validate(d)
        data.servidores_count = counts.get(d.id_delegacia, 0)
        result.append(data)
    return result


@router.get("/delegacias/{delegacia_id}")
def get_delegacia(delegacia_id: str, db: Session = Depends(get_db)):
    d = _get_delegacia_or_404(db, delegacia_id)
    count = db.query(Usuario).filter(Usuario.id_delegacia == d.id_delegacia).count()
    data = DelegaciaSchema.model_validate(d).model_dump()
    data["servidores_count"] = count
    return data


@router.post("/delegacias", response_model=DelegaciaSchema, status_code=201)
def create_delegacia(payload: DelegaciaCreateSchema, db: Session = Depends(get_db)):
    d = Delegacia(**payload.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.put("/delegacias/{delegacia_id}", response_model=DelegaciaSchema)
def update_delegacia(
    delegacia_id: str,
    payload: DelegaciaUpdateSchema,
    db: Session = Depends(get_db),
):
    d = _get_delegacia_or_404(db, delegacia_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(d, field, value)
    db.commit()
    db.refresh(d)
    return d


@router.put("/delegacias/{delegacia_id}/desativar", response_model=DelegaciaSchema)
def desativar_delegacia(delegacia_id: str, db: Session = Depends(get_db)):
    d = _get_delegacia_or_404(db, delegacia_id)
    d.ativo = False
    db.commit()
    db.refresh(d)
    return d
