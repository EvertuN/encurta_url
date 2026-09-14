"""Router de redirecionamento — GET /{short_code}."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as aioredis

from app.database.redis import get_redis
from app.database.session import get_db
from app.repositories import url_repo
from app.services import cache_service, metrics_service

router = APIRouter(tags=["Redirect"])


@router.get(
    "/{short_code}",
    summary="Redireciona para a URL original",
    response_class=RedirectResponse,
    status_code=status.HTTP_302_FOUND,
)
async def redirect(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> RedirectResponse:
    ip = metrics_service.extract_client_ip(request)
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    # 1. Tenta o cache primeiro (cache-aside)
    cached_url = await cache_service.cache_get(redis, short_code)
    if cached_url:
        background_tasks.add_task(
            metrics_service.record_click,
            short_code=short_code,
            ip=ip,
            user_agent=user_agent,
            referer=referer,
        )
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

    # 4. Registra métrica em background task
    background_tasks.add_task(
        metrics_service.record_click,
        short_code=short_code,
        ip=ip,
        user_agent=user_agent,
        referer=referer,
        url_id=url.id,
    )

    return RedirectResponse(url=url.original_url, status_code=status.HTTP_302_FOUND)
