"""Unit tests for app.utils.formatting.mask_cpf (LGPD Art. 46)."""
import pytest

from app.utils.formatting import mask_cpf

pytestmark = pytest.mark.unit


def test_mask_cpf_keeps_only_last_two_digits():
    assert mask_cpf("12345678909") == "***.***.***.09"


def test_mask_cpf_accepts_formatted_input():
    assert mask_cpf("123.456.789-09") == "***.***.***.09"


@pytest.mark.parametrize("invalid", ["123", "", "abcdefghijk", "1234567890"])
def test_mask_cpf_invalid_returns_fully_masked(invalid):
    assert mask_cpf(invalid) == "***.***.***-**"
