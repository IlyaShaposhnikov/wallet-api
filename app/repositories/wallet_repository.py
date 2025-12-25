from decimal import Decimal
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models import Wallet


class WalletRepository:
    """Репозиторий для операций с кошельками."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_wallet(
            self, wallet_id: str, for_update: bool = False
    ) -> Optional[Wallet]:
        """
        Получить кошелек по ID.

        :param wallet_id: UUID кошелька
        :param for_update: Если True, блокирует запись для обновления
        (SELECT FOR UPDATE)
        :return: Объект Wallet или None
        """
        query = select(Wallet).where(Wallet.id == wallet_id)

        if for_update:
            query = query.with_for_update()

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_wallet(self, wallet_id: str) -> Wallet:
        """
        Создать новый кошелек с начальным балансом 0.

        :param wallet_id: UUID кошелька
        :return: Созданный объект Wallet
        """
        wallet = Wallet(id=wallet_id, balance=Decimal('0.00'))
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet

    async def update_balance(
        self,
        wallet_id: str,
        operation_type: str,
        amount: Decimal
    ) -> Optional[Wallet]:
        """
        Изменить баланс кошелька с проверкой на достаточность средств.

        :param wallet_id: UUID кошелька
        :param operation_type: 'DEPOSIT' или 'WITHDRAW'
        :param amount: Сумма операции
        :return: Обновленный объект Wallet или None в случае ошибки
        :raises ValueError: При недостаточном балансе или неверной операции
        """
        try:
            # Начинаем транзакцию и блокируем запись
            wallet = await self.get_wallet(wallet_id, for_update=True)

            if not wallet:
                # Если кошелек не существует, создаем его (для пополнения)
                if operation_type == "DEPOSIT":
                    wallet = await self.create_wallet(wallet_id)
                else:
                    raise ValueError("Wallet not found")

            if operation_type == "DEPOSIT":
                wallet.balance += amount
            elif operation_type == "WITHDRAW":
                if wallet.balance < amount:
                    raise ValueError("Insufficient funds")
                wallet.balance -= amount
            else:
                raise ValueError("Invalid operation type")

            await self.db.commit()
            await self.db.refresh(wallet)
            return wallet

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e
        except ValueError as e:
            await self.db.rollback()
            raise e
