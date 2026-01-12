# Wallet REST API

Приложение предоставляет REST API для работы с балансом пользовательских кошельков.

## Быстрый старт

### 1. Клонирование и настройка
```bash
git clone git@github.com:IlyaShaposhnikov/wallet-api.git
cd wallet-api
# (Для локальной разработки вне Docker, если нужно)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
Создайте файл `.env` в корне проекта, основываясь на примере `.env.example`. Это позволит вам настроить параметры подключения к базе данных.
Если файл `.env` отсутствует, будут использованы значения по умолчанию, определённые в `app/config.py`.

### 3. Запуск в Docker
```bash
docker-compose up --build
```
Приложение будет доступно по адресу: http://localhost:8080 (http://127.0.0.1:8080)

### 4. Документация API
После запуска откройте: http://localhost:8080/docs (http://127.0.0.1:8080/docs)

## Основные функции API
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

## Тестирование
Запуск тестов
```bash
docker-compose up tests
```

## Технологии
- FastAPI - асинхронный веб-фреймворк
- SQLAlchemy 2.0 + asyncpg - асинхронная работа с PostgreSQL
- Alembic - миграции базы данных
- Docker & Docker Compose - контейнеризация
- Pytest + httpx - тестирование
- Pydantic v2 - валидация данных

## Конкурентность
Приложение гарантирует корректную работу при параллельных запросах благодаря:
- Транзакциям уровня READ COMMITTED
- Блокировкам SELECT FOR UPDATE
- Атомарным операциям изменения баланса

## Структура проекта
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

## Автор
Шапошников Илья
ilia.a.shaposhnikov@gmail.com
