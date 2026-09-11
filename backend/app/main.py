"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.redis import redis_lifespan
from app.routes import redirect, urls


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with redis_lifespan():
        yield


app = FastAPI(
    title="encurtaurl",
    description="Serviço moderno de encurtamento de URLs.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — a ordem importa: redirect por último para não engolir outras rotas
app.include_router(urls.router)
app.include_router(redirect.router)


@app.get("/health", tags=["Health"], summary="Verifica se a API está no ar")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
