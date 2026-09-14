"""Serviço de métricas — registro assíncrono de eventos de clique."""

import ipaddress
import logging
import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.repositories import click_repo, url_repo

logger = logging.getLogger(__name__)


def extract_client_ip(request: Request) -> str | None:
    """Extrai e valida o IP do cliente (suporta X-Forwarded-For e request.client)."""
    forwarded = request.headers.get("x-forwarded-for")
    raw_ip = (
        forwarded.split(",")[0].strip()
        if forwarded
        else (request.client.host if request.client else None)
    )
    if not raw_ip:
        return None
    try:
        ipaddress.ip_address(raw_ip)
        return raw_ip
    except ValueError:
        return None


async def record_click(
    short_code: str,
    ip: str | None = None,
    user_agent: str | None = None,
    referer: str | None = None,
    url_id: uuid.UUID | None = None,
    db: AsyncSession | None = None,
) -> None:
    """Registra o clique no banco de dados.

    Se uma sessão db for fornecida, utiliza-a diretamente.
    Caso contrário (execução em background task após a resposta),
    abre uma nova sessão isolada via AsyncSessionLocal.
    """
    try:
        if db is not None:
            await _persist_click(db, short_code, ip, user_agent, referer, url_id)
        else:
            async with AsyncSessionLocal() as session:
                await _persist_click(
                    session, short_code, ip, user_agent, referer, url_id
                )
    except Exception:
        logger.exception(
            "Falha ao registrar evento de clique para short_code=%s", short_code
        )


async def _persist_click(
    session: AsyncSession,
    short_code: str,
    ip: str | None,
    user_agent: str | None,
    referer: str | None,
    url_id: uuid.UUID | None,
) -> None:
    target_url_id = url_id
    if target_url_id is None:
        url = await url_repo.get_url_by_code(session, short_code)
        if url is None:
            return
        target_url_id = url.id

    await click_repo.create_click_event(
        db=session,
        url_id=target_url_id,
        ip=ip,
        user_agent=user_agent,
        referer=referer,
    )
