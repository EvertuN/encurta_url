"""Testes de integração — Consulta e Estatísticas (GET /urls/{code} e GET /urls/{code}/stats)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_url_info_returns_200(client: AsyncClient):
    """GET /urls/{code} deve retornar 200 com informações completas da URL."""
    create = await client.post("/urls", json={"original_url": "https://example.com/info"})
    assert create.status_code == 201
    created_data = create.json()
    short_code = created_data["short_code"]

    res = await client.get(f"/urls/{short_code}")
    assert res.status_code == 200
    data = res.json()

    assert data["id"] == created_data["id"]
    assert data["short_code"] == short_code
    assert data["original_url"] == "https://example.com/info"
    assert data["short_url"] == created_data["short_url"]
    assert data["created_at"] is not None
    assert data["expires_at"] is None


@pytest.mark.asyncio
async def test_get_url_info_not_found_returns_404(client: AsyncClient):
    """GET /urls/{code} com código inexistente deve retornar 404."""
    res = await client.get("/urls/naoexiste999")
    assert res.status_code == 404
    assert "não encontrado" in res.json()["detail"]


@pytest.mark.asyncio
async def test_get_url_stats_zero_clicks(client: AsyncClient):
    """GET /urls/{code}/stats com zero cliques deve retornar total_clicks=0 e last_click=null."""
    create = await client.post("/urls", json={"original_url": "https://example.com/zero-clicks"})
    short_code = create.json()["short_code"]

    res = await client.get(f"/urls/{short_code}/stats")
    assert res.status_code == 200
    data = res.json()

    assert data["short_code"] == short_code
    assert data["total_clicks"] == 0
    assert data["last_click"] is None


@pytest.mark.asyncio
async def test_get_url_stats_with_clicks(client: AsyncClient):
    """GET /urls/{code}/stats após N acessos deve refletir contagem e timestamp do último clique."""
    create = await client.post("/urls", json={"original_url": "https://example.com/multiple-clicks"})
    short_code = create.json()["short_code"]

    # Simula 3 acessos
    for _ in range(3):
        redirect_res = await client.get(f"/{short_code}", follow_redirects=False)
        assert redirect_res.status_code == 302

    res = await client.get(f"/urls/{short_code}/stats")
    assert res.status_code == 200
    data = res.json()

    assert data["short_code"] == short_code
    assert data["total_clicks"] == 3
    assert data["last_click"] is not None


@pytest.mark.asyncio
async def test_get_url_stats_not_found_returns_404(client: AsyncClient):
    """GET /urls/{code}/stats para código inexistente deve retornar 404."""
    res = await client.get("/urls/naoexiste999/stats")
    assert res.status_code == 404
    assert "não encontrado" in res.json()["detail"]
