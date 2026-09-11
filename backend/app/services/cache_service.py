"""Cache-aside sobre Redis para URLs encurtadas."""

import redis.asyncio as aioredis

from app.config import settings

_KEY_PREFIX = "url:"


def _key(short_code: str) -> str:
    return f"{_KEY_PREFIX}{short_code}"


async def cache_get(redis: aioredis.Redis, short_code: str) -> str | None:
    """Retorna a URL original do cache, ou None se não existir."""
    return await redis.get(_key(short_code))


async def cache_set(
    redis: aioredis.Redis,
    short_code: str,
    original_url: str,
    ttl: int | None = None,
) -> None:
    """Armazena a URL original no cache com TTL configurável."""
    effective_ttl = ttl if ttl is not None else settings.cache_ttl
    await redis.set(_key(short_code), original_url, ex=effective_ttl)


async def cache_delete(redis: aioredis.Redis, short_code: str) -> None:
    """Remove a entrada do cache (usado na exclusão de URL)."""
    await redis.delete(_key(short_code))
