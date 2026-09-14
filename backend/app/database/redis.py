"""Conexão Redis — cliente singleton gerenciado pelo lifespan do FastAPI."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis

from app.config import settings

# Instância global — inicializada no lifespan
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Dependência FastAPI que retorna o cliente Redis ativo."""
    if _redis_client is None:
        raise RuntimeError("Redis não inicializado — verifique o lifespan da aplicação")
    return _redis_client


@asynccontextmanager
async def redis_lifespan() -> AsyncGenerator[None, None]:
    """Context manager que abre e fecha a conexão Redis."""
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield
    finally:
        await _redis_client.aclose()
        _redis_client = None
