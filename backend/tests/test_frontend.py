"""Testes de integração — Frontend (GET /)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_root_serves_frontend(client: AsyncClient):
    """GET / deve retornar 200 e servir o HTML da interface."""
    res = await client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "encurtaurl" in res.text
    assert "shorten-form" in res.text
    assert "stats-form" in res.text
