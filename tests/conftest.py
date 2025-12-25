import asyncio
import os
from typing import AsyncGenerator, Generator

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
    poolclass=NullPool,  # Отключаем пул соединений для тестов
)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession, autoflush=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для получения сессии тестовой БД."""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Переопределяем зависимость get_db в приложении для тестов
app.dependency_overrides[get_db] = override_get_db


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
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Тестовые таблицы созданы")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        raise

    yield

    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("Тестовые таблицы удалены")
    except Exception as e:
        print(f"Ошибка при удалении таблиц: {e}")
    finally:
        # Закрываем все соединения
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

    def override_get_db_for_test():
        async def _override_get_db():
            yield db_session

        return _override_get_db

    # Временно переопределяем get_db для этого конкретного клиента
    app.dependency_overrides[get_db] = override_get_db_for_test()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", timeout=30.0
    ) as ac:
        yield ac

    # Восстанавливаем оригинальную зависимость
    app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def multiple_clients():
    """Фикстура для создания нескольких клиентов для конкурентных тестов."""
    clients = []
    for _ in range(5):
        # Создаем отдельную сессию для каждого клиента
        session = TestAsyncSessionLocal()

        def override_get_db_for_client():
            async def _override_get_db():
                yield session

            return _override_get_db

        app.dependency_overrides[get_db] = override_get_db_for_client()

        client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test",
            timeout=30.0
        )
        clients.append((client, session))

    yield [c[0] for c in clients]  # Возвращаем только клиентов

    for client, session in clients:
        await client.aclose()
        await session.close()

    # Восстанавливаем оригинальную зависимость
    app.dependency_overrides[get_db] = override_get_db
