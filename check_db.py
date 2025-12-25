# check_db.py
import asyncio
import asyncpg
import sys


async def check_db():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            conn = await asyncpg.connect(
                'postgresql://wallet_user:wallet_password@test_db:5432/wallet_test_db'
            )
            # Проверяем, что можем выполнить запрос
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            print(f'Попытка {attempt + 1}: Подключение к БД успешно')
            return True
        except Exception as e:
            print(f'Попытка {attempt + 1}: Ошибка подключения к БД: {e}')
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
    return False

if __name__ == '__main__':
    success = asyncio.run(check_db())
    sys.exit(0 if success else 1)
