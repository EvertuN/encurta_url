"""Fixtures compartilhadas entre todos os testes de integração."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database.session import Base, get_db
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Engine de teste — usa o mesmo banco que a aplicação."""
    engine = create_async_engine(settings.database_url)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(db_engine):
    """Sessão de banco com rollback automático ao fim de cada teste."""
    Session = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db):
    """AsyncClient HTTP que usa a sessão de teste injetada via DI."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
