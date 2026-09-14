"""Router de URLs — operações sobre o recurso URL."""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.redis import get_redis
from app.database.session import get_db
from app.repositories import url_repo
from app.schemas.url import UrlCreate, UrlInfo, UrlResponse, UrlStats
from app.services import url_service
from app.services.url_service import (
    ShortCodeCollisionError,
    ShortCodeConflictError,
    create_short_url,
)

router = APIRouter(prefix="/urls", tags=["URLs"])


def _to_response(url, base_url: str) -> UrlResponse:
    return UrlResponse(
        id=url.id,
        short_code=url.short_code,
        original_url=url.original_url,
        short_url=f"{base_url.rstrip('/')}/{url.short_code}",
        created_at=url.created_at,
        expires_at=url.expires_at,
    )


@router.post(
    "",
    response_model=UrlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma URL curta",
)
async def create_url(
    payload: UrlCreate,
    db: AsyncSession = Depends(get_db),
) -> UrlResponse:
    try:
        url = await create_short_url(db, payload)
    except ShortCodeConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except ShortCodeCollisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    return _to_response(url, settings.base_url)


@router.get(
    "/{short_code}/stats",
    response_model=UrlStats,
    summary="Consulta estatísticas de acesso de uma URL",
)
async def get_url_stats(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> UrlStats:
    stats = await url_repo.get_url_stats(db, short_code)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código '{short_code}' não encontrado.",
        )
    return UrlStats(**stats)


@router.get(
    "/{short_code}",
    response_model=UrlInfo,
    summary="Consulta informações detalhadas de uma URL",
)
async def get_url_info(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> UrlInfo:
    url = await url_repo.get_url_by_code(db, short_code)
    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código '{short_code}' não encontrado.",
        )
    return _to_response(url, settings.base_url)


@router.delete(
    "/{short_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma URL encurtada",
)
async def delete_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> None:
    deleted = await url_service.delete_url(db, redis, short_code)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código '{short_code}' não encontrado.",
        )
