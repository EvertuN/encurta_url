"""Serviço de URLs — orquestra geração, persistência e ciclo de vida de URLs."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as aioredis

from app.config import settings
from app.models.url import Url
from app.repositories import url_repo
from app.schemas.url import UrlCreate
from app.services import cache_service
from app.services.shortcode import generate_short_code


class ShortCodeCollisionError(Exception):
    """Levantado quando não é possível gerar um código único após N tentativas."""


class ShortCodeConflictError(Exception):
    """Levantado quando o custom_code solicitado já está em uso."""


async def create_short_url(db: AsyncSession, payload: UrlCreate) -> Url:
    """Cria uma URL curta com retry automático em caso de colisão.

    - Se ``payload.custom_code`` foi fornecido, tenta usá-lo diretamente.
    - Caso contrário, gera automaticamente e retenta até ``max_retries`` vezes.

    Raises:
        ShortCodeConflictError: custom_code já existe no banco.
        ShortCodeCollisionError: impossível gerar código único após max_retries.
    """
    original_url = str(payload.original_url)

    if payload.custom_code:
        # Código personalizado: uma única tentativa, erro explícito se colidir
        existing = await url_repo.get_url_by_code(db, payload.custom_code)
        if existing:
            raise ShortCodeConflictError(
                f"O código '{payload.custom_code}' já está em uso."
            )
        return await url_repo.create_url(
            db,
            original_url=original_url,
            short_code=payload.custom_code,
            expires_at=payload.expires_at,
        )

    # Código gerado automaticamente com retry em colisão
    for attempt in range(1, settings.short_code_max_retries + 1):
        code = generate_short_code()
        try:
            return await url_repo.create_url(
                db,
                original_url=original_url,
                short_code=code,
                expires_at=payload.expires_at,
            )
        except IntegrityError:
            await db.rollback()
            if attempt == settings.short_code_max_retries:
                raise ShortCodeCollisionError(
                    f"Não foi possível gerar um código único após "
                    f"{settings.short_code_max_retries} tentativas."
                )

    # Nunca atingido — satisfaz o type checker
    raise ShortCodeCollisionError("Falha inesperada na geração de short_code.")


async def delete_url(
    db: AsyncSession,
    redis: aioredis.Redis,
    short_code: str,
) -> bool:
    """Remove a URL do banco e invalida a chave no cache Redis.

    Retorna True se a URL existia e foi removida, False se não encontrada.
    """
    deleted = await url_repo.delete_url(db, short_code)
    if not deleted:
        return False

    await cache_service.cache_delete(redis, short_code)
    return True
