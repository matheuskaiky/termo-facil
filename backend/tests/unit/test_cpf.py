"""Unit tests for the CPF validator (cpf lib + fallback) in utils/cpf_utils.py."""
import pytest

from app.utils.cpf_utils import cpf_valido, _fallback_valido, digits

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("valid", ["11144477735", "111.444.777-35", "12345678909"])
def test_cpf_valido_accepts_valid(valid):
    assert cpf_valido(valid) is True


@pytest.mark.parametrize("invalid", [
    "11111111111",   # all same digits
    "12345678900",   # wrong check digits
    "123",           # too short
    "abcdefghijk",   # non-numeric
    "",
])
def test_cpf_valido_rejects_invalid(invalid):
    assert cpf_valido(invalid) is False


@pytest.mark.parametrize("valid", ["11144477735", "111.444.777-35", "12345678909"])
def test_fallback_matches_lib(valid):
    # The pure-Python fallback must agree with the library on validity.
    assert _fallback_valido(digits(valid)) is True
