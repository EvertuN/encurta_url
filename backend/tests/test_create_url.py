"""Testes de integração — POST /urls."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_url_returns_201(client: AsyncClient):
    """POST /urls com URL válida deve retornar 201 e o corpo correto."""
    response = await client.post("/urls", json={"original_url": "https://exemplo.com"})

    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == "https://exemplo.com/"
    assert len(data["short_code"]) == 6
    assert data["short_url"].endswith(f"/{data['short_code']}")
    assert data["expires_at"] is None


@pytest.mark.asyncio
async def test_create_url_with_custom_code(client: AsyncClient):
    """POST /urls com custom_code deve usar exatamente o código fornecido."""
    response = await client.post(
        "/urls",
        json={"original_url": "https://custom.com", "custom_code": "meulink"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == "meulink"
    assert data["short_url"].endswith("/meulink")


@pytest.mark.asyncio
async def test_create_url_duplicate_custom_code_returns_409(client: AsyncClient):
    """Dois requests com o mesmo custom_code devem resultar em 409 no segundo."""
    payload = {"original_url": "https://dup.com", "custom_code": "dupcode"}
    r1 = await client.post("/urls", json=payload)
    assert r1.status_code == 201

    r2 = await client.post("/urls", json=payload)
    assert r2.status_code == 409
    assert "dupcode" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_create_url_invalid_url_returns_422(client: AsyncClient):
    """URL inválida deve retornar 422 (Unprocessable Entity)."""
    response = await client.post("/urls", json={"original_url": "nao-e-uma-url"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_url_custom_code_too_short_returns_422(client: AsyncClient):
    """custom_code com menos de 4 caracteres deve retornar 422."""
    response = await client.post(
        "/urls",
        json={"original_url": "https://exemplo.com", "custom_code": "ab"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_url_custom_code_special_chars_returns_422(client: AsyncClient):
    """custom_code com caracteres especiais deve retornar 422."""
    response = await client.post(
        "/urls",
        json={"original_url": "https://exemplo.com", "custom_code": "meu-link"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_url_with_expiry(client: AsyncClient):
    """POST /urls com expires_at deve persistir a data de expiração."""
    response = await client.post(
        "/urls",
        json={
            "original_url": "https://expiry.com",
            "expires_at": "2099-12-31T23:59:59Z",
        },
    )
    assert response.status_code == 201
    assert response.json()["expires_at"] is not None
