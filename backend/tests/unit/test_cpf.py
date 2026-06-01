"""Unit tests for the CPF check-digit validator in processos.py."""
import pytest

from app.api.endpoints.processos import _validar_cpf

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("valid", ["11144477735", "111.444.777-35", "12345678909"])
def test_validar_cpf_accepts_valid(valid):
    assert _validar_cpf(valid) is True


@pytest.mark.parametrize("invalid", [
    "11111111111",   # all same digits
    "12345678900",   # wrong check digits
    "123",           # too short
    "abcdefghijk",   # non-numeric
    "",
])
def test_validar_cpf_rejects_invalid(invalid):
    assert _validar_cpf(invalid) is False
