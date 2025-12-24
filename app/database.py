from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import declarative_base

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Асинхронный генератор, предоставляющий сессию БД для каждого запроса.
    Сессия автоматически закрывается после использования.
    """
    async with AsyncSessionLocal() as session:
        yield session
