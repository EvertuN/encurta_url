"""Testes de integração — Remoção de URL (DELETE /urls/{code})."""

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.click_event import ClickEvent


@pytest.mark.asyncio
async def test_delete_url_returns_204(client: AsyncClient):
    """DELETE /urls/{code} para URL existente deve retornar 204 e torná-la inacessível."""
    # 1. Cria a URL
    create = await client.post(
        "/urls", json={"original_url": "https://example.com/delete-me"}
    )
    assert create.status_code == 201
    short_code = create.json()["short_code"]

    # 2. Deleta a URL
    delete_res = await client.delete(f"/urls/{short_code}")
    assert delete_res.status_code == 204
    assert delete_res.content == b""

    # 3. Consulta de informações deve retornar 404
    info_res = await client.get(f"/urls/{short_code}")
    assert info_res.status_code == 404

    # 4. Redirecionamento deve retornar 404
    redirect_res = await client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_url_invalidates_redis_cache(client: AsyncClient, fake_redis):
    """Remoção da URL deve obrigatoriamente invalidar a chave correspondente no Redis."""
    create = await client.post(
        "/urls", json={"original_url": "https://example.com/cache-del"}
    )
    short_code = create.json()["short_code"]

    # Primeiro acesso para popular o cache
    await client.get(f"/{short_code}", follow_redirects=False)
    cached = await fake_redis.get(f"url:{short_code}")
    assert cached == "https://example.com/cache-del"

    # Deleta a URL
    del_res = await client.delete(f"/urls/{short_code}")
    assert del_res.status_code == 204

    # Verifica se a chave foi expurgada do cache Redis
    cached_after = await fake_redis.get(f"url:{short_code}")
    assert cached_after is None

    # Redirecionamento não deve servir do cache
    res = await client.get(f"/{short_code}", follow_redirects=False)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_url_not_found_returns_404(client: AsyncClient):
    """DELETE /urls/{code} para código inexistente deve retornar 404."""
    res = await client.delete("/urls/codigo_inexistente_999")
    assert res.status_code == 404
    assert "não encontrado" in res.json()["detail"]


@pytest.mark.asyncio
async def test_delete_url_cascades_clicks(client: AsyncClient, db: AsyncSession):
    """Exclusão da URL deve remover em cascata os click_events associados no banco."""
    create = await client.post(
        "/urls", json={"original_url": "https://example.com/cascade"}
    )
    data = create.json()
    short_code = data["short_code"]
    url_id = UUID(data["id"])

    # Registra clique
    await client.get(f"/{short_code}", follow_redirects=False)
    clicks = (
        (await db.execute(select(ClickEvent).where(ClickEvent.url_id == url_id)))
        .scalars()
        .all()
    )
    assert len(clicks) == 1

    # Deleta a URL
    del_res = await client.delete(f"/urls/{short_code}")
    assert del_res.status_code == 204

    # Eventos de clique devem ter sido removidos em cascata
    clicks_after = (
        (await db.execute(select(ClickEvent).where(ClickEvent.url_id == url_id)))
        .scalars()
        .all()
    )
    assert len(clicks_after) == 0
