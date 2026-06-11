# Booking Service

REST API для бронирования переговорных комнат в коворкинге.

## Возможности

- JWT-аутентификация (логин/пароль → токен с ограниченным сроком действия)
- Роли: **employee** (сотрудник) и **admin** (администратор)
- Просмотр комнат и доступных слотов на конкретную дату
- Создание и отмена бронирований
- Изоляция данных: сотрудник видит только свои брони, администратор — все
- Хранение данных в PostgreSQL, миграции через Alembic

## Технологический стек

- **Python 3.11**, **FastAPI**, **SQLAlchemy 2.0** (async), **asyncpg**
- **PostgreSQL** как основная база данных
- **Alembic** для миграций схемы
- **python-jose** для JWT, **bcrypt** для хеширования паролей
- **pytest** + **pytest-asyncio** + **httpx** для тестирования (SQLite in-memory)

## Структура проекта

```
booking-service/
├── app/
│   ├── api/v1/          # Маршруты (auth, rooms, bookings)
│   ├── core/            # Безопасность (JWT, bcrypt)
│   ├── models/          # SQLAlchemy ORM модели
│   ├── repositories/    # Слой доступа к данным
│   ├── schemas/         # Pydantic схемы запросов/ответов
│   ├── services/        # Бизнес-логика
│   ├── config.py        # Настройки приложения
│   ├── database.py      # Подключение к БД
│   └── main.py          # Точка входа FastAPI
├── tests/
│   ├── unit/            # Юнит-тесты (сервисы, безопасность)
│   └── integration/     # Интеграционные тесты API
├── alembic/             # Миграции базы данных
├── Dockerfile
└── docker-compose.yml
```

## Локальный запуск

### Требования

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- PostgreSQL (или Docker для запуска БД)

### 1. Установка зависимостей

```bash
poetry install
```

### 2. Настройка окружения

```bash
cp .env.example .env
# Отредактируйте .env: укажите DATABASE_URL и SECRET_KEY
```

### 3. Запуск PostgreSQL через Docker (опционально)

```bash
docker run -d \
  --name booking-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=booking \
  -p 5432:5432 \
  postgres:16-alpine
```

### 4. Запуск приложения

```bash
poetry run uvicorn app.main:app --reload
```

При первом запуске автоматически создаются таблицы и добавляются тестовые данные:

| Логин | Пароль | Роль |
|-------|--------|------|
| `admin` | `admin123` | Администратор |
| `employee` | `employee123` | Сотрудник |

Также создаются две переговорных комнаты со слотами.

### 5. Документация API

После запуска откройте: **http://localhost:8000/docs**

## Запуск тестов

```bash
poetry run pytest -v
```

Тесты используют SQLite in-memory — PostgreSQL не требуется.

```
tests/unit/test_security.py           # Тесты JWT и bcrypt
tests/unit/test_booking_service.py    # Юнит-тесты сервиса бронирований
tests/integration/test_auth.py        # Регистрация, логин, токены
tests/integration/test_rooms.py       # CRUD комнат и слотов
tests/integration/test_bookings.py    # Бронирования, права доступа
```

## Запуск через Docker

```bash
docker run -d \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/booking \
  -e SECRET_KEY=your-secret-key \
  -p 8000:8000 \
  booking-service
```

## API Endpoints

### Аутентификация

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/auth/register` | Регистрация пользователя |
| `POST` | `/api/v1/auth/login` | Получение JWT-токена |
| `GET` | `/api/v1/auth/me` | Информация о текущем пользователе |

### Комнаты

| Метод | Путь | Роль | Описание |
|-------|------|------|----------|
| `GET` | `/api/v1/rooms` | Все | Список всех комнат |
| `POST` | `/api/v1/rooms` | Admin | Создать комнату |
| `GET` | `/api/v1/rooms/{id}` | Все | Данные комнаты со слотами |
| `PATCH` | `/api/v1/rooms/{id}` | Admin | Обновить комнату |
| `DELETE` | `/api/v1/rooms/{id}` | Admin | Удалить комнату |
| `POST` | `/api/v1/rooms/{id}/slots` | Admin | Добавить слот |
| `DELETE` | `/api/v1/rooms/{id}/slots/{slot_id}` | Admin | Удалить слот |
| `GET` | `/api/v1/rooms/availability?date=YYYY-MM-DD` | Все | Доступные слоты на дату |

### Бронирования

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/v1/bookings` | Мои брони (admin: все) |
| `POST` | `/api/v1/bookings` | Создать бронирование |
| `GET` | `/api/v1/bookings/{id}` | Детали бронирования |
| `DELETE` | `/api/v1/bookings/{id}` | Отменить бронирование |

## Примеры использования

### Получение токена

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "employee", "password": "employee123"}'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Просмотр доступности на дату

```bash
curl http://localhost:8000/api/v1/rooms/availability?date=2025-03-15 \
  -H "Authorization: Bearer <token>"
```

```json
[
  {
    "room": {
      "id": "...",
      "name": "Переговорная Альфа",
      "capacity": 10,
      "slots": [...]
    },
    "available_slots": [
      {"id": "...", "start_time": "09:00", "end_time": "11:00"},
      {"id": "...", "start_time": "13:00", "end_time": "15:00"}
    ]
  }
]
```

### Создание бронирования

```bash
curl -X POST http://localhost:8000/api/v1/bookings \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "<room_uuid>",
    "slot_id": "<slot_uuid>",
    "date": "2025-03-15"
  }'
```

### Отмена бронирования

```bash
curl -X DELETE http://localhost:8000/api/v1/bookings/<booking_id> \
  -H "Authorization: Bearer <token>"
```

## Миграции (для продакшена)

При использовании PostgreSQL в продакшене вместо `create_all` следует применять Alembic:

```bash
# Создать миграцию
poetry run alembic revision --autogenerate -m "initial"

# Применить миграции
poetry run alembic upgrade head
```
