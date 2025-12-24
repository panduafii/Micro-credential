from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.deps import get_db_session
from src.api.main import app
from src.domain.reference_data import QUESTION_TEMPLATES, ROLE_DEFINITIONS
from src.infrastructure.db.base import Base
from src.infrastructure.db.models import QuestionTemplate, RoleCatalog


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def test_client(event_loop: asyncio.AbstractEventLoop) -> Iterator[TestClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _init_db() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            await seed_reference_data(session)

    event_loop.run_until_complete(_init_db())

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_db_session, None)
    event_loop.run_until_complete(engine.dispose())


async def seed_reference_data(session: AsyncSession) -> None:
    role_count = await session.scalar(select(RoleCatalog.id).limit(1))
    if role_count:
        return

    for role in ROLE_DEFINITIONS:
        session.add(RoleCatalog(**role))
    await session.flush()

    for template in QUESTION_TEMPLATES:
        session.add(QuestionTemplate(**template))
    await session.commit()
