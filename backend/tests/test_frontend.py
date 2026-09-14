"""Testes de integração — Frontend (GET / e GET /admin)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_root_serves_frontend(client: AsyncClient):
    """GET / deve retornar 200 com o HTML da interface principal."""
    res = await client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "EncurtaURL" in res.text
    assert "shorten-btn" in res.text


@pytest.mark.asyncio
async def test_get_admin_serves_stats_page(client: AsyncClient):
    """GET /admin deve retornar 200 com o HTML da página de estatísticas."""
    res = await client.get("/admin")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "Estatísticas" in res.text
    assert "stats-panel" in res.text
