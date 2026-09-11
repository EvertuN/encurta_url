"""Repositório de URLs — operações de banco de dados."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.url import Url


async def create_url(
    db: AsyncSession,
    original_url: str,
    short_code: str,
    expires_at: datetime | None = None,
) -> Url:
    """Insere uma nova URL no banco e retorna o objeto persistido."""
    url = Url(
        id=uuid.uuid4(),
        short_code=short_code,
        original_url=original_url,
        expires_at=expires_at,
    )
    db.add(url)
    await db.commit()
    await db.refresh(url)
    return url


async def get_url_by_code(db: AsyncSession, short_code: str) -> Url | None:
    """Busca uma URL pelo short_code. Retorna None se não encontrada."""
    result = await db.execute(select(Url).where(Url.short_code == short_code))
    return result.scalar_one_or_none()


async def get_url_by_id(db: AsyncSession, url_id: uuid.UUID) -> Url | None:
    """Busca uma URL pelo id (UUID)."""
    return await db.get(Url, url_id)
