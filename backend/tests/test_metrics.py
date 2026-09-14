"""Testes de integração — Coleta de Métricas (Click Events)."""

from unittest.mock import MagicMock
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.click_event import ClickEvent
from app.services.metrics_service import extract_client_ip, record_click


@pytest.mark.asyncio
async def test_click_event_recorded_on_redirect(client: AsyncClient, db: AsyncSession):
    """Acesso a uma URL válida deve persistir um ClickEvent com metadados."""
    # 1. Cria a URL
    create_res = await client.post("/urls", json={"original_url": "https://example.com/metrics"})
    assert create_res.status_code == 201
    data = create_res.json()
    short_code = data["short_code"]
    url_id = UUID(data["id"])

    # 2. Acessa o link com headers
    headers = {
        "User-Agent": "TestBrowser/2.0",
        "Referer": "https://google.com/search",
        "X-Forwarded-For": "203.0.113.195",
    }
    response = await client.get(f"/{short_code}", headers=headers, follow_redirects=False)
    assert response.status_code == 302

    # 3. Verifica no banco se o evento foi gravado
    result = await db.execute(select(ClickEvent).where(ClickEvent.url_id == url_id))
    events = result.scalars().all()

    assert len(events) == 1
    event = events[0]
    assert event.url_id == url_id
    assert event.user_agent == "TestBrowser/2.0"
    assert event.referer == "https://google.com/search"
    assert str(event.ip) == "203.0.113.195"
    assert event.clicked_at is not None


@pytest.mark.asyncio
async def test_click_recorded_on_cache_hit(client: AsyncClient, db: AsyncSession):
    """Cliques devem ser contabilizados tanto no cache miss quanto no cache hit."""
    create_res = await client.post("/urls", json={"original_url": "https://example.com/cache-hit"})
    assert create_res.status_code == 201
    data = create_res.json()
    short_code = data["short_code"]
    url_id = UUID(data["id"])

    # Primeiro acesso (cache miss)
    r1 = await client.get(f"/{short_code}", follow_redirects=False)
    assert r1.status_code == 302

    # Segundo acesso (cache hit)
    r2 = await client.get(f"/{short_code}", follow_redirects=False)
    assert r2.status_code == 302

    # Ambos os acessos devem ter gerado eventos
    result = await db.execute(select(ClickEvent).where(ClickEvent.url_id == url_id))
    events = result.scalars().all()
    assert len(events) == 2


@pytest.mark.asyncio
async def test_click_event_not_recorded_on_404(client: AsyncClient, db: AsyncSession):
    """Acesso a código inexistente (404) não deve registrar click events."""
    res = await client.get("/inexistente999", follow_redirects=False)
    assert res.status_code == 404

    result = await db.execute(select(ClickEvent))
    events = result.scalars().all()
    assert not any(e.url_id == UUID("00000000-0000-0000-0000-000000000000") for e in events)


def test_extract_client_ip():
    """Valida a extração e filtragem de IPs válidos e inválidos."""
    # Com X-Forwarded-For contendo múltiplos IPs
    req1 = MagicMock()
    req1.headers = {"x-forwarded-for": "198.51.100.25, 10.0.0.1"}
    assert extract_client_ip(req1) == "198.51.100.25"

    # Com IPv6 válido
    req2 = MagicMock()
    req2.headers = {"x-forwarded-for": "2001:db8::1"}
    assert extract_client_ip(req2) == "2001:db8::1"

    # Com IP inválido
    req3 = MagicMock()
    req3.headers = {"x-forwarded-for": "invalid-ip-string"}
    assert extract_client_ip(req3) is None

    # Sem header, usando request.client
    req4 = MagicMock()
    req4.headers = {}
    req4.client.host = "192.168.1.100"
    assert extract_client_ip(req4) == "192.168.1.100"

    # Sem header e sem client
    req5 = MagicMock()
    req5.headers = {}
    req5.client = None
    assert extract_client_ip(req5) is None


@pytest.mark.asyncio
async def test_record_click_nonexistent_url(db: AsyncSession):
    """record_click para código que não existe no banco não deve lançar exceção."""
    # Não deve lançar exceção
    await record_click(short_code="codigo_fantasma", db=db)
