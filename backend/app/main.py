"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.database.redis import redis_lifespan
from app.routes import redirect, urls

# Diretório do frontend (suporta ambiente local e Docker)
_FRONTEND_DIR = Path("/frontend")
if not _FRONTEND_DIR.exists() or not (_FRONTEND_DIR / "index.html").exists():
    _FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


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


@app.get("/health", tags=["Health"], summary="Verifica se a API está no ar")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.get("/", include_in_schema=False)
async def serve_index():
    index_file = _FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"status": "ok", "app": "encurtaurl"})


@app.get("/admin", include_in_schema=False)
async def serve_admin():
    admin_file = _FRONTEND_DIR / "admin.html"
    if admin_file.exists():
        return FileResponse(admin_file)
    return JSONResponse({"detail": "admin not found"}, status_code=404)


# Routers — a ordem importa: redirect por último para não engolir rotas raiz
app.include_router(urls.router)
app.include_router(redirect.router)
