import uuid
from sqlalchemy import Column, Numeric, String
from app.database import Base


class Wallet(Base):
    """
    Модель, представляющая таблицу 'wallets' в базе данных.
    Каждый кошелек имеет уникальный идентификатор и баланс.
    """
    __tablename__ = "wallets"

    id = Column(
        String, primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    balance = Column(
        Numeric(precision=12, scale=2), nullable=False, default=0.00
    )

    def __repr__(self) -> str:
        return f"<Wallet(id='{self.id}', balance={self.balance})>"
