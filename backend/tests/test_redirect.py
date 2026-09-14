"""Testes de integração — GET /{short_code} (redirecionamento com cache)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_redirect_returns_302(client: AsyncClient):
    """Criar uma URL e depois acessá-la deve retornar 302."""
    # Cria a URL
    create = await client.post(
        "/urls", json={"original_url": "https://redirect-test.com"}
    )
    assert create.status_code == 201
    short_code = create.json()["short_code"]

    # Acessa o código — não seguir o redirect
    response = await client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://redirect-test.com/"


@pytest.mark.asyncio
async def test_redirect_cache_hit(client: AsyncClient, fake_redis):
    """Segundo acesso deve vir do cache (sem nova consulta ao banco)."""
    create = await client.post("/urls", json={"original_url": "https://cache-hit.com"})
    short_code = create.json()["short_code"]

    # Primeiro acesso — popula o cache
    r1 = await client.get(f"/{short_code}", follow_redirects=False)
    assert r1.status_code == 302

    # Verifica que o Redis foi populado
    cached = await fake_redis.get(f"url:{short_code}")
    assert cached == "https://cache-hit.com/"

    # Segundo acesso — deve vir do cache
    r2 = await client.get(f"/{short_code}", follow_redirects=False)
    assert r2.status_code == 302
    assert r2.headers["location"] == "https://cache-hit.com/"


@pytest.mark.asyncio
async def test_redirect_not_found_returns_404(client: AsyncClient):
    """Código inexistente deve retornar 404."""
    response = await client.get("/codigoinexistente", follow_redirects=False)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_redirect_serves_from_cache_without_db(client: AsyncClient, fake_redis):
    """Se a URL está no cache, o banco não é consultado."""
    # Injeta direto no cache sem passar pelo banco
    await fake_redis.set("url:direto", "https://apenas-cache.com")

    response = await client.get("/direto", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://apenas-cache.com"
