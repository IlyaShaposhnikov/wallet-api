import asyncio

import pytest
from httpx import AsyncClient


class TestWalletAPI:
    """Тесты для эндпоинтов работы с кошельками."""

    async def test_health_check(self, client: AsyncClient):
        """Тест эндпоинта проверки здоровья."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_get_nonexistent_wallet(self, client: AsyncClient):
        """Тест получения несуществующего кошелька."""
        wallet_id = "non-existent-uuid"
        response = await client.get(f"/api/v1/wallets/{wallet_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_deposit_to_new_wallet(self, client: AsyncClient):
        """
        Тест пополнения нового кошелька
        (должен автоматически создать кошелек).
        """
        wallet_id = "test-wallet-1"

        # Пополняем несуществующий кошелек
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 1000.50},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["wallet_id"] == wallet_id
        assert data["operation_type"] == "DEPOSIT"
        assert data["amount"] == 1000.50
        assert data["new_balance"] == 1000.50

        # Проверяем, что баланс сохранился
        response = await client.get(f"/api/v1/wallets/{wallet_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 1000.50

    async def test_deposit_and_withdraw(self, client: AsyncClient):
        """Тест последовательных операций пополнения и списания."""
        wallet_id = "test-wallet-2"

        # Пополняем
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 2000.00},
        )
        assert response.status_code == 200
        assert response.json()["new_balance"] == 2000.00

        # Списываем
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 500.00},
        )
        assert response.status_code == 200
        assert response.json()["new_balance"] == 1500.00

        # Проверяем итоговый баланс
        response = await client.get(f"/api/v1/wallets/{wallet_id}")
        assert response.status_code == 200
        assert response.json()["balance"] == 1500.00

    async def test_withdraw_insufficient_funds(self, client: AsyncClient):
        """Тест списания при недостаточном балансе."""
        wallet_id = "test-wallet-3"

        # Сначала пополняем
        await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 300.00},
        )

        # Пытаемся списать больше, чем есть
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 500.00},
        )

        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()

    async def test_withdraw_from_nonexistent_wallet(self, client: AsyncClient):
        """Тест списания с несуществующего кошелька."""
        wallet_id = "non-existent-wallet"

        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 100.00},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_invalid_operation_type(self, client: AsyncClient):
        """Тест некорректного типа операции."""
        wallet_id = "test-wallet-4"

        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "INVALID", "amount": 100.00},
        )

        # FastAPI автоматически валидирует enum, поэтому 422
        assert response.status_code == 422

    async def test_negative_amount(self, client: AsyncClient):
        """Тест отрицательной суммы."""
        wallet_id = "test-wallet-5"

        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": -100.00},
        )

        assert response.status_code == 422  # Валидация Pydantic

    async def test_zero_amount(self, client: AsyncClient):
        """Тест нулевой суммы."""
        wallet_id = "test-wallet-6"

        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 0.00},
        )

        assert response.status_code == 422  # Валидация Pydantic

    @pytest.mark.asyncio
    async def test_concurrent_deposits(self, multiple_clients):
        """
        Тест конкурентных пополнений одного кошелька.
        Проверяем, что баланс корректно суммируется.
        """
        wallet_id = "concurrent-wallet-test-1"

        # Используем первый клиент для создания кошелька
        first_client = multiple_clients[0]

        # Создаем кошелек с начальным балансом
        response = await first_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 1000.00},
        )
        assert response.status_code == 200
        assert response.json()["new_balance"] == 1000.00

        # Запускаем несколько конкурентных пополнений разными клиентами
        async def make_deposit(client: AsyncClient, amount: float):
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "DEPOSIT", "amount": amount},
            )
            return response

        # Используем клиенты с 1 по 4 (0-й уже использовали)
        tasks = []
        for i, client in enumerate(multiple_clients[1:5], 1):
            task = asyncio.create_task(make_deposit(client, 100.00))
            tasks.append(task)

        # Ждем завершения всех задач
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем, что все запросы успешны
        for response in responses:
            if isinstance(response, Exception):
                pytest.fail(f"Запрос упал с ошибкой: {response}")
            assert response.status_code == 200

        # Проверяем итоговый баланс (1000 + 4*100 = 1400)
        response = await first_client.get(f"/api/v1/wallets/{wallet_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 1400.00, f"Ожидался баланс 1400.00, получен {data['balance']}"

    @pytest.mark.asyncio
    async def test_concurrent_withdrawals(self, multiple_clients):
        """
        Тест конкурентных списаний.
        Проверяем, что не возникает race condition.
        """
        wallet_id = "concurrent-withdraw-wallet-test-2"
        first_client = multiple_clients[0]

        # Создаем кошелек с большим балансом
        response = await first_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 1000.00},
        )
        assert response.status_code == 200
        assert response.json()["new_balance"] == 1000.00

        # Функция для списания
        async def make_withdraw(client: AsyncClient, amount: float):
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "WITHDRAW", "amount": amount},
            )
            return response

        # Запускаем 3 одновременных списания разными клиентами по 200
        tasks = []
        for i, client in enumerate(multiple_clients[1:4], 1):
            task = asyncio.create_task(make_withdraw(client, 200.00))
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем результаты
        success_count = 0
        for response in responses:
            if isinstance(response, Exception):
                # Если это исключение из-за недостатка средств, это нормально
                # для конкурентных операций, но у нас баланса должно хватить
                continue
            if response.status_code == 200:
                success_count += 1

        # Все три списания должны быть успешны
        assert success_count == 3, f"Успешных списаний: {success_count}, ожидалось 3"

        # Проверяем итоговый баланс (1000 - 3*200 = 400)
        response = await first_client.get(f"/api/v1/wallets/{wallet_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 400.00, f"Ожидался баланс 400.00, получен {data['balance']}"

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self, multiple_clients):
        """
        Тест конкурентных операций разных типов.
        Проверяем корректность итогового баланса.
        """
        wallet_id = "concurrent-mixed-wallet-test-3"
        first_client = multiple_clients[0]

        # Создаем кошелек с начальным балансом
        response = await first_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 500.00},
        )
        assert response.status_code == 200
        assert response.json()["new_balance"] == 500.00

        # Определяем операции для выполнения
        operations = [
            ("DEPOSIT", 100.00),
            ("WITHDRAW", 50.00),
            ("DEPOSIT", 200.00),
            ("WITHDRAW", 150.00),
        ]

        async def perform_operation(
                client: AsyncClient, op_type: str, amount: float
        ):
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": op_type, "amount": amount},
            )
            return response

        # Запускаем все операции одновременно разными клиентами
        tasks = []
        for i, (op_type, amount) in enumerate(operations):
            client = multiple_clients[i % len(multiple_clients)]
            task = asyncio.create_task(
                perform_operation(client, op_type, amount)
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем результаты
        success_count = 0
        for response in responses:
            if isinstance(response, Exception):
                continue
            if response.status_code == 200:
                success_count += 1

        # Все операции должны быть успешны
        assert success_count == 4, f"Успешных операций: {success_count}, ожидалось 4"

        # Проверяем итоговый баланс (500 + 100 - 50 + 200 - 150 = 600)
        response = await first_client.get(f"/api/v1/wallets/{wallet_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 600.00, f"Ожидался баланс 600.00, получен {data['balance']}"

    async def test_amount_with_two_decimals(self, client: AsyncClient):
        """Тест суммы с 2 знаками после запятой (должно работать)."""
        wallet_id = "two-decimals-wallet"

        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 100.12},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 100.12
        assert data["new_balance"] == 100.12
