from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OperationType(str, Enum):
    """Типы операций с кошельком."""

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperationRequest(BaseModel):
    """Схема для запроса на изменение баланса."""

    operation_type: OperationType
    amount: float = Field(gt=0, description="Сумма должна быть положительной")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Валидация суммы: проверка на 2 знака после запятой."""
        if v <= 0:
            raise ValueError("Amount must be positive")

        decimal_amount = Decimal(str(v))
        if decimal_amount.as_tuple().exponent < -2:
            raise ValueError("Amount must have at most 2 decimal places")

        return decimal_amount


class WalletResponse(BaseModel):
    """Схема для ответа с информацией о кошельке."""

    model_config = ConfigDict(from_attributes=True)

    wallet_id: str
    balance: float


class OperationResponse(BaseModel):
    """Схема для ответа об операции."""

    wallet_id: str
    operation_type: OperationType
    amount: float
    new_balance: float
    message: str = "Operation successful"
