"""Router de redirecionamento — GET /{short_code}."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as aioredis

from app.database.redis import get_redis
from app.database.session import get_db
from app.repositories import url_repo
from app.services import cache_service

router = APIRouter(tags=["Redirect"])


@router.get(
    "/{short_code}",
    summary="Redireciona para a URL original",
    response_class=RedirectResponse,
    status_code=status.HTTP_302_FOUND,
)
async def redirect(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> RedirectResponse:
    # 1. Tenta o cache primeiro (cache-aside)
    cached_url = await cache_service.cache_get(redis, short_code)
    if cached_url:
        return RedirectResponse(url=cached_url, status_code=status.HTTP_302_FOUND)

    # 2. Cache MISS — consulta o banco
    url = await url_repo.get_url_by_code(db, short_code)
    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código '{short_code}' não encontrado.",
        )

    # 3. Popula o cache para próximas requisições
    await cache_service.cache_set(redis, short_code, url.original_url)

    return RedirectResponse(url=url.original_url, status_code=status.HTTP_302_FOUND)
