import asyncio
import os
from typing import AsyncGenerator, Generator, List

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine
)
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app

# Используем тестовую БД с NullPool для избежания проблем с конкурентностью
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://wallet_user:wallet_password@test_db:5432/wallet_test_db",
)

# Создаем движок с NullPool для тестов
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession, autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создание event loop для асинхронных тестов."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Создание и удаление таблиц перед и после каждого теста."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Тестовые таблицы созданы")

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Тестовые таблицы удалены")

    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для получения сессии БД."""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client(
    db_session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для создания асинхронного клиента тестирования."""
    def override_get_db():
        async def _override_get_db():
            yield db_session
        return _override_get_db

    app.dependency_overrides[get_db] = override_get_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=30.0
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def multiple_clients() -> List[AsyncClient]:
    """
    Создание нескольких независимых клиентов для конкурентных тестов.
    Каждый клиент имеет свою собственную сессию БД.
    """
    clients = []
    sessions = []

    for i in range(5):
        # Создаем новую сессию для каждого клиента
        session = TestAsyncSessionLocal()
        sessions.append(session)

        # Создаем новое приложение для каждого клиента, чтобы избежать
        # конфликтов зависимостей
        from fastapi import FastAPI
        from app.main import app as original_app

        # Создаем новое приложение для каждого клиента
        client_app = FastAPI()

        # Копируем маршруты из оригинального приложения
        client_app.include_router(original_app.router)

        # Создаем уникальную зависимость для этого клиента
        def create_get_db(session=session):
            async def get_db_override():
                yield session
            return get_db_override

        # Переопределяем зависимость для этого конкретного приложения
        client_app.dependency_overrides[get_db] = create_get_db()

        # Создаем клиента для этого приложения
        client = AsyncClient(
            transport=ASGITransport(app=client_app),
            base_url="http://test",
            timeout=30.0
        )
        clients.append(client)

    yield clients

    # Закрываем всех клиентов и сессии
    for client in clients:
        await client.aclose()
    for session in sessions:
        await session.close()
