"""Testes de integração dos models ORM (requer PostgreSQL via Docker)."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.click_event import ClickEvent
from app.models.url import Url


@pytest_asyncio.fixture(scope="function")
async def db():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_url_persisted_and_retrieved(db: AsyncSession):
    url = Url(id=uuid.uuid4(), short_code="abc123", original_url="https://exemplo.com")
    db.add(url)
    await db.commit()

    fetched = await db.get(Url, url.id)
    assert fetched is not None
    assert fetched.short_code == "abc123"
    assert fetched.original_url == "https://exemplo.com"
    assert fetched.created_at is not None
    assert fetched.expires_at is None


@pytest.mark.asyncio
async def test_short_code_uniqueness_constraint(db: AsyncSession):
    url1 = Url(id=uuid.uuid4(), short_code="dup001", original_url="https://a.com")
    url2 = Url(id=uuid.uuid4(), short_code="dup001", original_url="https://b.com")  # mesmo código
    db.add(url1)
    await db.flush()
    db.add(url2)

    with pytest.raises(IntegrityError):
        await db.flush()


@pytest.mark.asyncio
async def test_click_event_with_valid_fk(db: AsyncSession):
    url = Url(id=uuid.uuid4(), short_code="fk001", original_url="https://fk.com")
    db.add(url)
    await db.flush()

    event = ClickEvent(
        id=uuid.uuid4(),
        url_id=url.id,
        ip="192.168.0.1",
        user_agent="pytest/1.0",
        referer="https://origem.com",
    )
    db.add(event)
    await db.commit()

    fetched = await db.get(ClickEvent, event.id)
    assert fetched is not None
    assert fetched.url_id == url.id
    assert fetched.user_agent == "pytest/1.0"


@pytest.mark.asyncio
async def test_click_event_invalid_fk_raises(db: AsyncSession):
    event = ClickEvent(
        id=uuid.uuid4(),
        url_id=uuid.uuid4(),  # FK inexistente
        ip="10.0.0.1",
    )
    db.add(event)

    with pytest.raises(IntegrityError):
        await db.commit()
