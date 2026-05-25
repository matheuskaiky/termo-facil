from pydantic import BaseModel, field_validator
from datetime import date
from app.models import TipoDepoente


class NovoProcessoPayload(BaseModel):
    num_procedimento: str
    data_instauracao: date
    nome_depoente: str
    cpf_depoente: str
    tipo_depoente: TipoDepoente

    @field_validator("cpf_depoente", mode="before")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        from app.api.endpoints.processos import _validar_cpf
        if not _validar_cpf(v):
            raise ValueError("CPF inválido")
        return v
