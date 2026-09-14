"""Repositório de eventos de clique — persistência de métricas."""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.click_event import ClickEvent


async def create_click_event(
    db: AsyncSession,
    url_id: uuid.UUID,
    ip: str | None = None,
    user_agent: str | None = None,
    referer: str | None = None,
) -> ClickEvent:
    """Registra um evento de clique para uma URL."""
    event = ClickEvent(
        id=uuid.uuid4(),
        url_id=url_id,
        ip=ip,
        user_agent=user_agent,
        referer=referer,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
