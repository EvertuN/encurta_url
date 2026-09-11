"""Geração de códigos curtos criptograficamente seguros."""

import secrets
import string

from app.config import settings

# Caracteres permitidos no short_code: A-Z a-z 0-9
_ALPHABET = string.ascii_letters + string.digits
_ALPHABET_LEN = len(_ALPHABET)


def generate_short_code(length: int | None = None) -> str:
    """Gera um código curto aleatório usando secrets (CSPRNG).

    Args:
        length: Tamanho do código. Usa ``settings.short_code_length`` por padrão.

    Returns:
        String alfanumérica de ``length`` caracteres.

    Raises:
        ValueError: Se ``length`` for menor que 4.
    """
    n = length if length is not None else settings.short_code_length

    if n < 4:
        raise ValueError(f"short_code length must be >= 4, got {n}")

    # secrets.choice é CSPRNG — adequado para geração de tokens únicos
    return "".join(secrets.choice(_ALPHABET) for _ in range(n))


def is_valid_short_code(code: str) -> bool:
    """Verifica se um código contém apenas caracteres permitidos e tem tamanho mínimo."""
    return (
        isinstance(code, str)
        and len(code) >= 4
        and all(c in _ALPHABET for c in code)
    )
