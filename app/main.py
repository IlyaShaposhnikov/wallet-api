from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum

app = FastAPI(
    title="Wallet API",
    description="API для управления балансом кошельков",
    version="1.0.0"
)


class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperation(BaseModel):
    operation_type: OperationType
    amount: float


@app.get("/api/v1/wallets/{wallet_id}")
async def get_balance(wallet_id: str):
    """Получение баланса кошелька."""
    return {"wallet_id": wallet_id, "balance": 0.0}


@app.post("/api/v1/wallets/{wallet_id}/operation")
async def perform_operation(wallet_id: str, operation: WalletOperation):
    """Изменение баланса кошелька."""
    return {
        "wallet_id": wallet_id,
        "operation": operation.operation_type,
        "amount": operation.amount,
        "message": "Operation received"
    }


@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работы сервера."""
    return {"message": "Wallet API is running"}
