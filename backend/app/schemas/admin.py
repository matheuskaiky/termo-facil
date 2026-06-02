from pydantic import BaseModel, UUID4, field_validator
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
    tipo: Optional[str] = None
    sigla: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = None
    cod_ibge: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    ativo: bool = True
    servidores_count: Optional[int] = None

    class Config:
        from_attributes = True


def _uppercase_nome(v: str) -> str:
    """RN: o nome da unidade é sempre armazenado em MAIÚSCULAS."""
    if v is None:
        return v
    v = " ".join(v.strip().split())  # colapsa espaços
    return v.upper()


class DelegaciaCreateSchema(BaseModel):
    nome_unidade: str
    # Endereço obrigatório (RN). complemento/bairro/cod_ibge são opcionais
    # porque CEPs de cidade inteira podem não ter logradouro/bairro.
    cep: str
    logradouro: str
    numero: str
    municipio: str
    uf: str
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cod_ibge: Optional[str] = None
    tipo: Optional[str] = None
    sigla: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    ativo: bool = True

    @field_validator("nome_unidade")
    @classmethod
    def _nome_upper(cls, v: str) -> str:
        v = _uppercase_nome(v)
        if not v or len(v) < 3:
            raise ValueError("Nome da unidade deve ter ao menos 3 caracteres.")
        return v

    @field_validator("cep")
    @classmethod
    def _cep_fmt(cls, v: str) -> str:
        digits = "".join(c for c in (v or "") if c.isdigit())
        if len(digits) != 8:
            raise ValueError("CEP deve conter 8 dígitos.")
        return f"{digits[:5]}-{digits[5:]}"

    @field_validator("uf")
    @classmethod
    def _uf_upper(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if len(v) != 2:
            raise ValueError("UF inválida.")
        return v

    @field_validator("sigla")
    @classmethod
    def _sigla_upper(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        return " ".join(v.strip().split()).upper()


class DelegaciaUpdateSchema(BaseModel):
    """Todos os campos opcionais — atualização parcial."""
    nome_unidade: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = None
    cod_ibge: Optional[str] = None
    tipo: Optional[str] = None
    sigla: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    ativo: Optional[bool] = None

    @field_validator("nome_unidade")
    @classmethod
    def _nome_upper(cls, v: Optional[str]) -> Optional[str]:
        return _uppercase_nome(v) if v is not None else v

    @field_validator("uf")
    @classmethod
    def _uf_upper(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v else v

    @field_validator("sigla")
    @classmethod
    def _sigla_upper(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return " ".join(v.strip().split()).upper() or None

class UsuarioSchema(BaseModel):
    id_usuario: UUID4
    matricula: str
    nome: str
    id_delegacia: UUID4
    must_change_password: bool = False
    ativo: bool = True
    delegacia: Optional[DelegaciaSchema] = None
    cargo: Optional[CargoSchema] = None

    class Config:
        from_attributes = True


class UsuarioStatusSchema(BaseModel):
    ativo: bool


class UsuarioCreateSchema(BaseModel):
    matricula: str
    nome: str
    id_delegacia: UUID4
    id_cargo: UUID4


class UsuarioUpdateSchema(BaseModel):
    nome: Optional[str] = None
    id_delegacia: Optional[UUID4] = None
    id_cargo: Optional[UUID4] = None
    ativo: Optional[bool] = None


class TempPasswordUserResponse(BaseModel):
    temp_password: str
    id_usuario: UUID4
    matricula: str
    nome: str

class UsuarioUpdateCargoSchema(BaseModel):
    id_cargo: UUID4

class CargoUpdatePermissoesSchema(BaseModel):
    permissoes_ids: List[UUID4]
