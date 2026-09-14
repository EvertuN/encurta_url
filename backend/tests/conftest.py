"""Fixtures compartilhadas entre todos os testes de integração."""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.database.session as app_db_session
from app.config import settings
from app.database.redis import get_redis
from app.database.session import get_db
from app.main import app


class FakeRedis:
    """Redis em memória para testes — sem dependência de servidor real."""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(settings.database_url)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def patch_async_session_local(db_engine):
    """Garante que AsyncSessionLocal use o engine e event loop do teste atual."""
    original_session = app_db_session.AsyncSessionLocal
    app_db_session.AsyncSessionLocal = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    yield
    app_db_session.AsyncSessionLocal = original_session
    await app_db_session.engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_database(db_engine):
    """Garante banco de dados limpo e isolamento entre os testes."""
    from sqlalchemy import text

    async with db_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE click_events, urls CASCADE;"))
    yield


@pytest_asyncio.fixture(scope="function")
async def db(db_engine):
    Session = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def fake_redis():
    return FakeRedis()


@pytest_asyncio.fixture(scope="function")
async def client(db, fake_redis):
    """AsyncClient com DI overrides: banco com rollback + Redis em memória."""

    async def override_get_db():
        yield db

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
