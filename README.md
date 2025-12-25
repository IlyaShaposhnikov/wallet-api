# Wallet REST API

Приложение предоставляет REST API для работы с балансом пользовательских кошельков.

## Быстрый старт

### 1. Клонирование и настройка
```bash
git clone git@github.com:IlyaShaposhnikov/wallet-api.git
cd wallet-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Запуск в Docker
```bash
docker-compose up --build
```
Приложение будет доступно по адресу: http://localhost:8080 (http://0.0.0.0:8080)

### 3. Документация API
После запуска откройте: http://localhost:8080/docs (http://0.0.0.0:8080/docs)

### Основные функции API
Получение баланса
```text
GET /api/v1/wallets/{wallet_id}
```
Изменение баланса
```text
POST /api/v1/wallets/{wallet_id}/operation
```
Тело запроса:

```json
{
  "operation_type": "DEPOSIT" или "WITHDRAW",
  "amount": 1000.50
}
```

### Тестирование
Запуск тестов
```bash
# Все тесты
docker-compose up tests

# Или локально
python -m pytest tests/ -v
```

### Технологии
- FastAPI - асинхронный веб-фреймворк
- SQLAlchemy 2.0 + asyncpg - асинхронная работа с PostgreSQL
- Alembic - миграции базы данных
- Docker & Docker Compose - контейнеризация
- Pytest + httpx - тестирование
- Pydantic v2 - валидация данных

### Конкурентность
Приложение гарантирует корректную работу при параллельных запросах благодаря:
- Транзакциям уровня REPEATABLE READ
- Блокировкам SELECT FOR UPDATE
- Атомарным операциям изменения баланса

### Структура проекта
```text
wallet-api/
├── app/
│   ├── repositories/     # Слой доступа к данным
│   ├── schemas.py        # Pydantic-схемы
│   ├── models.py         # Модели SQLAlchemy
│   ├── database.py       # Настройка БД
│   ├── config.py         # Конфигурация
│   └── main.py           # Основное приложение
├── tests/                # Тесты
├── alembic/              # Миграции
├── scripts/              # Вспомогательные скрипты
├── docker-compose.yml    # Docker-оркестрация
└── Dockerfile            # Docker образ
```

### Автор
Шапошников Илья
ilia.a.shaposhnikov@gmail.com
