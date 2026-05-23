from pydantic import BaseModel, UUID4
from typing import List, Optional

class PermissionSchema(BaseModel):
    id_permissao: UUID4
    nome_permissao: str
    descricao_permissao: str

    class Config:
        from_attributes = True

class CargoSchema(BaseModel):
    id_cargo: UUID4
    nome_cargo: str
    permissoes: List[PermissionSchema] = []

    class Config:
        from_attributes = True

class CargoCreateSchema(BaseModel):
    nome_cargo: str
    permissoes_ids: List[UUID4]

class DelegaciaSchema(BaseModel):
    id_delegacia: UUID4
    nome_unidade: str
    cod_sinesp: str

    class Config:
        from_attributes = True

class UsuarioSchema(BaseModel):
    id_usuario: UUID4
    matricula: str
    nome: str
    id_delegacia: UUID4
    must_change_password: bool = False
    delegacia: Optional[DelegaciaSchema] = None
    cargo: Optional[CargoSchema] = None

    class Config:
        from_attributes = True

class UsuarioUpdateCargoSchema(BaseModel):
    id_cargo: UUID4
