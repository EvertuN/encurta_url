"""Repositório de URLs — operações de banco de dados."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.click_event import ClickEvent
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


async def get_url_stats(db: AsyncSession, short_code: str) -> dict | None:
    """Retorna estatísticas de cliques de uma URL pelo short_code.

    Retorna None se a URL não for encontrada no banco.
    """
    query = (
        select(
            Url.short_code,
            func.count(ClickEvent.id).label("total_clicks"),
            func.max(ClickEvent.clicked_at).label("last_click"),
        )
        .outerjoin(ClickEvent, ClickEvent.url_id == Url.id)
        .where(Url.short_code == short_code)
        .group_by(Url.id, Url.short_code)
    )
    result = await db.execute(query)
    row = result.one_or_none()
    if row is None:
        return None

    return {
        "short_code": row.short_code,
        "total_clicks": row.total_clicks,
        "last_click": row.last_click,
    }


async def delete_url(db: AsyncSession, short_code: str) -> bool:
    """Remove uma URL pelo short_code. Retorna True se removida, False se não encontrada."""
    url = await get_url_by_code(db, short_code)
    if url is None:
        return False
    await db.delete(url)
    await db.commit()
    return True
