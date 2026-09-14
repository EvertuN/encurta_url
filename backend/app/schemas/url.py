"""Schemas Pydantic para o recurso URL."""

from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class UrlCreate(BaseModel):
    """Payload para criar uma URL curta."""

    original_url: AnyHttpUrl = Field(..., description="URL original a ser encurtada")
    custom_code: str | None = Field(
        default=None,
        min_length=4,
        max_length=12,
        description="Código personalizado opcional (4–12 caracteres alfanuméricos)",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Data/hora de expiração (opcional, timezone-aware)",
    )

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
        if not all(c in allowed for c in v):
            raise ValueError("custom_code deve conter apenas caracteres alfanuméricos")
        return v


class UrlResponse(BaseModel):
    """Representação pública de uma URL encurtada."""

    id: UUID
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class UrlInfo(UrlResponse):
    """Informações completas da URL encurtada."""

    pass


class UrlStats(BaseModel):
    """Estatísticas de acesso de uma URL encurtada."""

    short_code: str
    total_clicks: int
    last_click: datetime | None
