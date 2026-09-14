"""Testes unitários e de integração adicionais para services e edge cases."""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import url_repo
from app.schemas.url import UrlCreate
from app.services.url_service import (
    ShortCodeCollisionError,
    ShortCodeConflictError,
    create_short_url,
    delete_url,
)


@pytest.mark.asyncio
async def test_url_service_custom_code_conflict(db: AsyncSession):
    """Garante que ShortCodeConflictError é disparada quando o custom_code já existe."""
    payload = UrlCreate(original_url="https://exemplo1.com", custom_code="custom123")
    await create_short_url(db, payload)

    payload_dup = UrlCreate(
        original_url="https://exemplo2.com", custom_code="custom123"
    )
    with pytest.raises(ShortCodeConflictError) as exc:
        await create_short_url(db, payload_dup)
    assert "já está em uso" in str(exc.value)


@pytest.mark.asyncio
async def test_url_service_collision_retries_exhausted(db: AsyncSession):
    """Garante que ShortCodeCollisionError é disparada quando esgotam as tentativas."""
    payload = UrlCreate(original_url="https://retry-fail.com")

    with patch(
        "app.repositories.url_repo.create_url",
        side_effect=IntegrityError(
            "duplicate key", params=None, orig=Exception("unique")
        ),
    ):
        with pytest.raises(ShortCodeCollisionError) as exc:
            await create_short_url(db, payload)
        assert "Não foi possível gerar um código único" in str(exc.value)


@pytest.mark.asyncio
async def test_url_service_delete_nonexistent_url(db: AsyncSession, fake_redis):
    """delete_url deve retornar False quando a URL não existe."""
    result = await delete_url(db, fake_redis, "nonexistent999")
    assert result is False


@pytest.mark.asyncio
async def test_url_repo_nonexistent_returns_none_or_false(db: AsyncSession):
    """url_repo methods para códigos inexistentes devem se comportar adequadamente."""
    assert await url_repo.get_url_by_code(db, "inexistente") is None
    assert await url_repo.get_url_stats(db, "inexistente") is None
    assert await url_repo.delete_url(db, "inexistente") is False
