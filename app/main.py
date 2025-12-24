from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import engine, get_db
from app.config import settings
from app.models import Base
import asyncio

from pydantic import BaseModel
from enum import Enum


class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperation(BaseModel):
    operation_type: OperationType
    amount: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер lifespan управляет событиями запуска и остановки.
    При запуске создает таблицы в БД.
    """
    print("Starting up...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created/verified")
    except Exception as e:
        print(f"Note: Could not connect to database: {e}")
        print("This is expected during development without Docker")
    yield
    print("Shutting down...")
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API для управления балансом кошельков",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Проверяет, что приложение работает и может подключиться к БД."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy", "database": "disconnected", "error": str(e)
        }


@app.get("/api/v1/wallets/{wallet_id}")
async def get_balance(wallet_id: str, db: AsyncSession = Depends(get_db)):
    """Получение баланса кошелька."""
    return {"wallet_id": wallet_id, "balance": 0.0}


@app.post("/api/v1/wallets/{wallet_id}/operation")
async def perform_operation(
    wallet_id: str, operation: WalletOperation,
    db: AsyncSession = Depends(get_db)
):
    """Изменение баланса кошелька."""
    return {
        "wallet_id": wallet_id,
        "operation": operation.operation_type,
        "amount": operation.amount,
        "message": "Operation received (not implemented yet)"
    }


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Wallet API is running"}
