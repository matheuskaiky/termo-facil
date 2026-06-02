from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional
from app.models import TipoDepoente


class NovoProcessoPayload(BaseModel):
    num_procedimento: str
    data_instauracao: date
    nome_depoente: str
    cpf_depoente: str
    tipo_depoente: TipoDepoente

    # Endereço opcional do depoente (mesmos moldes da delegacia, via ViaCEP).
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = None
    cod_ibge: Optional[str] = None

    @field_validator("cpf_depoente", mode="before")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        from app.utils.cpf_utils import cpf_valido, digits
        if not cpf_valido(v):
            raise ValueError("CPF inválido")
        return digits(v)

    @field_validator("uf")
    @classmethod
    def _uf_upper(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v else v
