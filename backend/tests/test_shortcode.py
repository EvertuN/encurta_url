"""Testes unitários para o gerador de short_codes.

Estes testes não dependem de banco de dados nem de Docker —
rodam puramente em memória.
"""

import re

import pytest

from app.services.shortcode import generate_short_code, is_valid_short_code

ALPHANUM_RE = re.compile(r"^[A-Za-z0-9]+$")


class TestGenerateShortCode:
    def test_default_length(self):
        """Deve gerar código com o comprimento padrão (settings.short_code_length)."""
        code = generate_short_code()
        # Não hardcodamos o valor — apenas garantimos que é positivo e coerente
        assert len(code) >= 4

    def test_custom_length(self):
        """Deve respeitar o comprimento solicitado."""
        for length in (4, 6, 8, 12):
            code = generate_short_code(length=length)
            assert len(code) == length, f"Esperado {length}, obtido {len(code)}"

    def test_only_alphanumeric_characters(self):
        """Código deve conter apenas A-Z, a-z, 0-9."""
        for _ in range(50):
            code = generate_short_code()
            assert ALPHANUM_RE.match(code), f"Caractere inválido em: {code!r}"

    def test_uniqueness(self):
        """Chamadas repetidas devem produzir códigos distintos na grande maioria."""
        codes = {generate_short_code() for _ in range(200)}
        # Com 62^6 ≈ 56 bi combinações, colisão em 200 amostras é praticamente impossível
        assert len(codes) == 200

    def test_length_too_small_raises(self):
        """Comprimento < 4 deve levantar ValueError."""
        with pytest.raises(ValueError, match="must be >= 4"):
            generate_short_code(length=3)

    def test_zero_length_raises(self):
        with pytest.raises(ValueError):
            generate_short_code(length=0)


class TestIsValidShortCode:
    def test_valid_codes(self):
        assert is_valid_short_code("abc1") is True
        assert is_valid_short_code("ABC123") is True
        assert is_valid_short_code("aZ9bQr") is True

    def test_invalid_too_short(self):
        assert is_valid_short_code("ab") is False
        assert is_valid_short_code("") is False

    def test_invalid_special_chars(self):
        assert is_valid_short_code("abc-1") is False
        assert is_valid_short_code("abc_1") is False
        assert is_valid_short_code("abc 1") is False
        assert is_valid_short_code("abc/1") is False

    def test_invalid_type(self):
        assert is_valid_short_code(None) is False  # type: ignore[arg-type]
        assert is_valid_short_code(1234) is False  # type: ignore[arg-type]
