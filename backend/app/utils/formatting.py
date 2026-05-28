def mask_cpf(cpf: str) -> str:
    """
    Masks a CPF for API responses, keeping only the verification digits (last 2) visible.
    Full CPF remains in the database; API-layer protection per LGPD Art. 46.
    Encryption at rest is deferred to a future phase (requires pgcrypto migration).
    """
    digits = cpf.replace(".", "").replace("-", "")
    if len(digits) != 11 or not digits.isdigit():
        return "***.***.***-**"
    return f"***.***.***.{digits[9]}{digits[10]}"
