"""CPF helpers — validation via the `cpf` PyPI library, with a pure-Python fallback.

The fallback (módulo 11) is kept so the suite/app never hard-fails if the library
is unavailable in some environment.
"""
import re


def digits(cpf: str) -> str:
    return re.sub(r"\D", "", cpf or "")


def _fallback_valido(c: str) -> bool:
    if len(c) != 11 or c == c[0] * 11:
        return False

    def dig(base: str, peso_inicial: int) -> int:
        soma = sum(int(d) * p for d, p in zip(base, range(peso_inicial, 1, -1)))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    return c[9] == str(dig(c[:9], 10)) and c[10] == str(dig(c[:10], 11))


def cpf_valido(cpf: str) -> bool:
    c = digits(cpf)
    if len(c) != 11:
        return False
    try:
        import cpf as _cpf_lib  # PyPI package
        return bool(_cpf_lib.validate(c))
    except Exception:
        return _fallback_valido(c)


def formatar_cpf(cpf: str) -> str:
    c = digits(cpf)
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" if len(c) == 11 else (cpf or "")
