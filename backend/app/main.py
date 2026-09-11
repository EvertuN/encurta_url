from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="encurtaurl",
    description="Serviço moderno de encurtamento de URLs.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"], summary="Verifica se a API está no ar")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
