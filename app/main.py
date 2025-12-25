# app/main.py
from contextlib import asynccontextmanager
from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import engine, get_db
from app.config import settings
from app.repositories.wallet_repository import WalletRepository
from app.schemas import (
    WalletOperationRequest,
    WalletResponse,
    OperationResponse,
    OperationType
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер lifespan управляет событиями запуска и остановки.
    """
    print("Starting up...")
    # Таблицы создаются через миграции Alembic
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


@app.get(
    "/api/v1/wallets/{wallet_id}",
    response_model=WalletResponse,
    summary="Получить баланс кошелька",
    description="Возвращает текущий баланс указанного кошелька."
)
async def get_balance(wallet_id: str, db: AsyncSession = Depends(get_db)):
    """Получение баланса кошелька."""
    repo = WalletRepository(db)
    wallet = await repo.get_wallet(wallet_id)

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail=f"Wallet with id {wallet_id} not found"
        )

    return WalletResponse(
        wallet_id=wallet.id,
        balance=float(wallet.balance)
    )


@app.post(
    "/api/v1/wallets/{wallet_id}/operation",
    response_model=OperationResponse,
    summary="Изменить баланс кошелька",
    description="""
    Выполняет операцию пополнения (DEPOSIT) или списания (WITHDRAW) средств.

    Особенности:
    - Для WITHDRAW: проверяется достаточность баланса
    - Для DEPOSIT: если кошелек не существует, он будет создан
    - Операции атомарны и защищены от параллельного доступа
    (одновременных изменений, конкуренции за ресурсы)
    """
)
async def perform_operation(
    wallet_id: str,
    operation: WalletOperationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Изменение баланса кошелька."""
    try:
        repo = WalletRepository(db)

        wallet = await repo.update_balance(
            wallet_id=wallet_id,
            operation_type=operation.operation_type.value,
            amount=operation.amount
        )

        return OperationResponse(
            wallet_id=wallet.id,
            operation_type=operation.operation_type,
            amount=float(operation.amount),
            new_balance=float(wallet.balance)
        )

    except ValueError as e:
        error_msg = str(e)
        if "Insufficient funds" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Insufficient funds for withdrawal"
            )
        elif "Wallet not found" in error_msg:
            raise HTTPException(
                status_code=404,
                detail=f"Wallet with id {wallet_id} not found"
            )
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Wallet API is running"}
