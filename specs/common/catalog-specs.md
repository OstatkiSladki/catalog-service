# 📋 Техническая Спецификация Реализации
# Catalog Service

**Версия документа:** 1.0.0  
**Дата:** 2026-03-16  
**Статус:** Утверждено для реализации  
**Язык реализации:** Python 3.12+  
**Package Manager:** uv

---

## 1. Обзор и Назначение Документа

### 1.1. Цель Документа
Данный документ определяет полную техническую спецификацию для реализации **Catalog Service** — сервиса управления товарным каталогом, категориями, специальными предложениями (офферами) и отзывами пользователей. Спецификация предназначена для команды разработки и содержит исчерпывающие требования к архитектуре, структуре проекта, компонентам, интеграциям и процессам.

### 1.2. Область Применения
Спецификация охватывает:
- ✅ Структуру проекта и организацию кода
- ✅ Технологический стек и зависимости
- ✅ Слои архитектуры (API, Business, Data)
- ✅ Интеграции (API Gateway, Venue Service, Order Service, RabbitMQ)
- ✅ Безопасность и аутентификацию
- ✅ Логирование и наблюдаемость
- ✅ Тестирование и деплой

### 1.3. Контекст Архитектуры

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OrthoFlow Architecture                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────────────────┐ │
│  │   Client     │────▶│   Gateway    │────▶│   Catalog Service       │ │
│  │  (Mobile/    │     │    (Kong)    │     │   (Python/FastAPI)      │ │
│  │   Web)       │     │              │     │                         │ │
│  └──────────────┘     └──────────────┘     └───────────┬─────────────┘ │
│                                                         │               │
│                              ┌──────────────────────────┼──────────────┤
│                              │                          │              │
│                              ▼                          ▼              ▼
│                       ┌──────────────┐          ┌──────────────┐ ┌──────────┐
│                       │  PostgreSQL  │          │   RabbitMQ   │ │  Redis   │
│                       │ (db_catalog) │          │  (Events)    │ │ (Cache)  │
│                       └──────────────┘          └──────────────┘ └──────────┘
│                              │                          │
│                              ▼                          ▼
│                       ┌──────────────┐          ┌──────────────┐
│                       │ Venue Service│          │ Order Service│
│                       │   (gRPC)     │          │   (gRPC)     │
│                       └──────────────┘          └──────────────┘
└─────────────────────────────────────────────────────────────────────────┘
```

**Ключевые принципы:**
- **Database Per Service** — Catalog Service владеет `db_catalog` (schema: `catalog`)
- **Event-Driven** — Публикация событий в RabbitMQ для других сервисов
- **Identity Propagation** — Заголовки идентичности от API Gateway (`X-User-*`)
- **Soft Delete** — `deleted_at` вместо физического удаления
- **Audit Logging** — Все mutating операции логируются

---

## 2. Технологический Стек

### 2.1. Основные Технологии

| Компонент | Технология | Версия | Обоснование |
|-----------|------------|--------|-------------|
| Язык | Python | 3.12+ | Типизация, производительность, экосистема |
| Package Manager | uv | 0.5+ | Быстрая установка зависимостей, lock-файлы |
| Web Framework | FastAPI | 0.115+ | Автоматическая OpenAPI, асинхронность, валидация |
| ORM | SQLAlchemy | 2.0+ | Async support, типизация, миграции |
| Migrations | Alembic | 1.13+ | Версионирование схемы БД |
| Validation | Pydantic | 2.9+ | Валидация данных, сериализация |
| Message Broker | RabbitMQ | 3.12+ | Event streaming, асинхронная коммуникация |
| RabbitMQ Client | aio-pika | 9.4+ | Асинхронный клиент для Python |
| Cache | Redis | 7.2+ | Кэширование, rate limiting |
| Redis Client | redis-py | 5.0+ | Async support |
| gRPC Client | grpcio | 1.60+ | Внутрисервисная коммуникация |
| Security | python-jose | 3.3+ | JWT обработка (для локальной валидации) |

### 2.2. Зависимости (pyproject.toml)

```toml
[project]
name = "catalog-service"
version = "1.0.0"
description = "Catalog Service - Управление каталогом товаров и офферами"
requires-python = ">=3.12"

[project.dependencies]
# Web Framework
fastapi = "^0.115.0"
uvicorn = {version = "^0.32.0", extras = ["standard"]}

# Database
sqlalchemy = {version = "^2.0.35", extras = ["asyncio"]}
asyncpg = "^0.30.0"
alembic = "^1.13.0"

# Validation
pydantic = "^2.9.0"
pydantic-settings = "^2.6.0"

# Message Broker
aio-pika = "^9.4.0"

# Cache
redis = {version = "^5.0.0", extras = ["hiredis"]}

# gRPC
grpcio = "^1.60.0"
grpcio-tools = "^1.60.0"

# Observability
structlog = "^24.4.0"
opentelemetry-api = "^1.27.0"
opentelemetry-sdk = "^1.27.0"
opentelemetry-instrumentation-fastapi = "^0.48b0"
opentelemetry-exporter-otlp = "^1.27.0"
prometheus-client = "^0.21.0"

# Utilities
python-multipart = "^0.0.12"
httpx = "^0.27.0"
tenacity = "^9.0.0"

[tool.uv]
dev-dependencies = [
    "pytest = "^8.3.0",
    "pytest-asyncio = "^0.24.0",
    "pytest-cov = "^6.0.0",
    "factory-boy = "^3.3.0",
    "ruff = "^0.7.0",
    "mypy = "^1.12.0",
]
```

### 2.3. Инструменты Разработки

| Инструмент | Назначение | Конфигурация |
|------------|------------|--------------|
| uv | Управление зависимостями | uv.lock |
| ruff | Linting | ruff.toml |
| mypy | Static type checking | mypy.ini |
| pytest | Тестирование | pytest.ini |
| pre-commit | Git hooks | .pre-commit-config.yaml |

---

## 3. Структура Проекта

### 3.1. Directory Layout

```
catalog-service/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # CI pipeline
│       └── cd.yml                    # CD pipeline
├── .venv/                             # Virtual environment (uv)
├── alembic/
│   ├── versions/                     # Migration files
│   ├── env.py                        # Alembic environment
│   └── script.py.mako                # Migration template
├── src/
│   ├── __init__.py
│   ├── main.py                       # Application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py               # Configuration management
│   │   └── logging.py                # Logging configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                   # Dependencies (DI)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── categories.py
│   │   │   ├── products.py
│   │   │   ├── offers.py
│   │   │   ├── reviews.py
│   │   │   └── health.py
│   │   └── v1/
│   │       └── router.py             # API versioning
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                   # Base model class
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── product_category.py
│   │   ├── offer.py
│   │   ├── offer_item.py
│   │   └── review.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py                 # Common schemas (pagination, error)
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── offer.py
│   │   └── review.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── category_service.py
│   │   ├── product_service.py
│   │   ├── offer_service.py
│   │   ├── review_service.py
│   │   └── event_publisher.py        # RabbitMQ publishing
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                   # Base repository
│   │   ├── category_repository.py
│   │   ├── product_repository.py
│   │   ├── offer_repository.py
│   │   └── review_repository.py
│   ├── grpc_clients/
│   │   ├── __init__.py
│   │   ├── venue_client.py           # Venue Service gRPC client
│   │   └── order_client.py           # Order Service gRPC client
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                   # Identity headers validation
│   │   ├── logging.py                # Request/Response logging
│   │   ├── tracing.py                # OpenTelemetry integration
│   │   └── error_handler.py          # Global exception handling
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── pagination.py
│   │   └── validators.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── unit/
│       ├── integration/
│       └── e2e/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   ├── migrate.sh
│   └── seed.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
├── README.md
└── Makefile
```

### 3.2. Описание Ключевых Директорий

| Директория | Назначение | Ответственность |
|------------|------------|-----------------|
| `src/` | Исходный код сервиса | Вся бизнес-логика |
| `api/routes/` | HTTP endpoints | Маршрутизация запросов |
| `models/` | SQLAlchemy модели | ORM mapping к БД |
| `schemas/` | Pydantic схемы | Валидация request/response |
| `services/` | Business logic | Use cases, orchestration, events |
| `repositories/` | Data access | CRUD операции с БД |
| `grpc_clients/` | gRPC integration | Взаимодействие с Venue/Order Service |
| `middleware/` | Cross-cutting concerns | Auth, logging, tracing |
| `config/` | Configuration | Settings, environment |
| `tests/` | Test suites | Unit, integration, e2e |

---

## 4. Конфигурация и Настройки

### 4.1. Environment Variables

```bash
# Application
APP_NAME=catalog-service
APP_VERSION=1.0.0
APP_ENV=production  # development, staging, production
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8002
WORKERS=4
RELOAD=false

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/db_catalog
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30

# RabbitMQ
RABBITMQ_URL=amqp://user:password@rabbitmq:5672/
RABBITMQ_EVENT_EXCHANGE=catalog.events
RABBITMQ_PRODUCER_CONFIRM=true

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL=300

# gRPC Services
VENUE_SERVICE_HOST=venue-service:50051
ORDER_SERVICE_HOST=order-service:50052
GRPC_TIMEOUT=5

# Observability
OTEL_SERVICE_NAME=catalog-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security (from Gateway)
GATEWAY_TRUSTED_NETWORKS=10.0.0.0/8,172.16.0.0/12
```

### 4.2. Settings Management (`src/config/settings.py`)

**Задачи:**
- Централизованное управление конфигурацией
- Валидация переменных окружения при старте
- Поддержка разных окружений (dev/staging/prod)
- Type-safe configuration через Pydantic Settings

**Требования:**
- Использовать `pydantic-settings` для загрузки из .env
- Валидировать все обязательные переменные при инициализации
- Поддерживать hot-reload для development режима
- Шифровать чувствительные данные (DATABASE_URL, etc.)

### 4.3. Logging Configuration (`src/config/logging.py`)

**Задачи:**
- Структурированное логирование (JSON format)
- Correlation ID (`X-Request-ID`) в каждом логе
- Интеграция с OpenTelemetry для tracing
- Разные уровни логирования для разных окружений

**Формат Лога:**
```json
{
   "timestamp": "2026-03-16T10:30:00.000Z",
   "level": "INFO",
   "service": "catalog-service",
   "trace_id": "0-abc123def456",
   "span_id": "abc123",
   "request_id": "uuid-here",
   "user_id": "uuid-here",
   "action": "offer.created",
   "message": "Offer created successfully",
   "duration_ms": 45
}
```

---

## 5. Слои Архитектуры

### 5.1. Архитектурные Слои

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Layer (FastAPI)                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Routes / Controllers                                           │   │
│  │  - HTTP request/response handling                               │   │
│  │  - Input validation (Pydantic)                                  │   │
│  │  - Authentication (Gateway headers)                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────┤
│                        Service Layer (Business Logic)                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Services / Use Cases                                           │   │
│  │  - Business rules enforcement                                   │   │
│  │  - Transaction management                                       │   │
│  │  - Event publishing                                             │   │
│  │  - gRPC client calls (Venue, Order validation)                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────┤
│                       Repository Layer (Data Access)                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Repositories                                                   │   │
│  │  - CRUD operations                                              │   │
│  │  - Query building                                               │   │
│  │  - Soft delete handling                                         │   │
│  │  - Pagination                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────┤
│                          Infrastructure Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │
│  │   PostgreSQL    │  │    RabbitMQ     │  │       Redis         │   │
│  │  (db_catalog)   │  │   (Events)      │  │     (Cache)         │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2. API Layer

**Файл:** `src/api/v1/router.py`

**Задачи:**
- Регистрация всех route handlers
- Версионирование API (`/api/v1/`)
- Middleware подключение
- OpenAPI documentation generation

**Требования:**
- Все routes префиксированы `/api/v1/`
- Каждый route имеет tags для Swagger UI
- Response models строго типизированы
- Error responses стандартизированы

**Файл:** `src/api/deps.py`

**Задачи:**
- Dependency injection для FastAPI
- Извлечение identity headers от Gateway
- Валидация обязательных заголовков
- Предоставление context для services

**Извлекаемые Заголовки:**

| Заголовок | Тип | Обязательный | Описание |
|-----------|-----|-------------|----------|
| `X-User-ID` | string | ✅ | ID пользователя из auth_db |
| `X-User-Role` | enum | ✅ | Роль (user/staff/admin) |
| `X-User-Venue-ID` | integer | ⚠️ | Для staff (venue_id) |
| `X-Request-ID` | string | ✅ | Correlation ID для tracing |

### 5.3. Service Layer

**Назначение:** Бизнес-логика и orchestration

**Принципы:**
- **Single Responsibility** — Один service = один aggregate root
- **Transaction Management** — Все mutating операции в транзакции
- **Event Publishing** — Публикация событий после успешной транзакции
- **No Direct DB Access** — Только через repositories
- **gRPC Validation** — Валидация venue_id/user_id через внешние сервисы

**Интерфейсы Services:**

```
Interface CategoryService:
  - get_by_id(category_id: int) -> Category
  - list(filters, pagination) -> PaginatedResult[Category]
  - create(data: CategoryCreate, context: IdentityContext) -> Category
  - update(category_id: int, data: CategoryUpdate, context: IdentityContext) -> Category
  - archive(category_id: int, context: IdentityContext) -> None

Interface ProductService:
  - get_by_id(product_id: int) -> Product
  - list(filters, pagination) -> PaginatedResult[Product]
  - create(data: ProductCreate, context: IdentityContext) -> Product
  - update(product_id: int, data: ProductUpdate, context: IdentityContext) -> Product
  - archive(product_id: int, context: IdentityContext) -> None

Interface OfferService:
  - get_by_id(offer_id: int) -> Offer
  - list(filters, pagination) -> PaginatedResult[Offer]
  - create(data: OfferCreate, context: IdentityContext) -> Offer
  - update(offer_id: int, data: OfferUpdate, context: IdentityContext) -> Offer
  - cancel(offer_id: int, context: IdentityContext) -> None
  - check_availability(offer_ids: list[int]) -> AvailabilityResult

Interface ReviewService:
  - get_by_id(review_id: int) -> Review
  - list(filters, pagination) -> PaginatedResult[Review]
  - create(data: ReviewCreate, context: IdentityContext) -> Review
  - update(review_id: int, data: ReviewUpdate, context: IdentityContext) -> Review
  - archive(review_id: int, context: IdentityContext) -> None
```

**Бизнес-правила:**

| Сущность | Правило | Валидация |
|----------|---------|-----------|
| Category | Slug должен быть уникальным | DB unique constraint |
| Product | Минимум одна категория | Service validation |
| Offer | `current_price` < `original_price` | Service validation |
| Offer | `venue_id` должен существовать | gRPC Venue Service |
| Offer | `expires_at` > `now()` | Service validation |
| Review | Один отзыв на `order_id` | DB unique constraint |
| Review | `order_id` должен существовать | gRPC Order Service |
| Review | Только автор заказа может создать отзыв | Service validation |

### 5.4. Repository Layer

**Назначение:** Data access abstraction

**Принципы:**
- **One Repository per Aggregate** — CategoryRepository, ProductRepository, etc.
- **Base Repository** — Общие CRUD операции в базовом классе
- **Soft Delete** — Все queries фильтруют `deleted_at IS NULL`
- **Async Only** — Все методы асинхронные

**Базовый Интерфейс:**
```
Interface BaseRepository[T]:
  - get_by_id(id: int) -> Optional[T]
  - list(filters, pagination) -> Sequence[T]
  - count(filters) -> int
  - create(data) -> T
  - update(id: int, data) -> T
  - soft_delete(id: int) -> None
  - hard_delete(id: int) -> None  # Только для cleanup jobs
```

**Специфичные Методы:**

| Repository | Специфичные Методы |
|------------|-------------------|
| CategoryRepository | `get_tree()`, `get_children(parent_id)` |
| ProductRepository | `list_by_category(category_id)`, `search(query)` |
| OfferRepository | `list_by_venue(venue_id, status)`, `get_active_offers()` |
| ReviewRepository | `list_by_venue(venue_id)`, `get_by_order(order_id)` |

### 5.5. Event Publishing Layer

**Назначение:** Публикация domain events в RabbitMQ

**Важно:** Catalog Service НЕ отправляет уведомления напрямую. Вместо этого публикует события, которые потребляет Notification Service и другие сервисы.

**Файл:** `src/services/event_publisher.py`

**Задачи:**
- Асинхронная публикация событий в RabbitMQ
- Retry logic при временных ошибках broker
- Schema validation перед публикацией
- Correlation ID propagation

**Файл:** `src/events/topics.py`

**RabbitMQ Exchanges & Routing Keys:**

| Exchange | Routing Key | Описание | Consumers |
|----------|-------------|----------|-----------|
| `catalog.events` | `offer.created` | Создание оффера | Notification, Analytics |
| `catalog.events` | `offer.updated` | Обновление оффера | Notification, Analytics |
| `catalog.events` | `offer.expired` | Истечение срока оффера | Notification, Order |
| `catalog.events` | `offer.sold_out` | Оффер распродан | Notification, Order |
| `catalog.events` | `review.created` | Создание отзыва | Notification, Analytics |
| `catalog.events` | `product.created` | Создание товара | Analytics |
| `catalog.events` | `product.updated` | Обновление товара | Analytics |

**Event Schema:**
```json
{
   "event_id": "uuid",
   "event_type": "offer.created",
   "timestamp": "2026-03-16T10:30:00Z",
   "aggregate_id": "offer_id",
   "aggregate_type": "Offer",
   "payload": {
     "offer_id": "int",
     "venue_id": "int",
     "current_price": "decimal",
     "expires_at": "datetime"
   },
   "metadata": {
     "service_origin": "catalog-service",
     "trace_id": "opentelemetry-trace-id",
     "correlation_id": "request-uuid",
     "user_id": "uuid"
   }
}
```

---

## 6. Модели Данных

### 6.1. SQLAlchemy Models

**Файл:** `src/models/base.py`

**Базовый Класс:**
- Все модели наследуются от `Base`
- Автоматические поля: `id`, `created_at`, `updated_at`
- Soft delete support: `deleted_at`
- Async session support

**Модели (соответствуют catalog.sql):**

| Модель | Таблица | Ключевые Поля | Soft Delete |
|--------|---------|---------------|-------------|
| Category | `categories` | id, name, slug, parent_id, is_active | deleted_at |
| Product | `products` | id, name, description, image_urls, characteristics_json | deleted_at |
| ProductCategory | `product_categories` | id, product_id, category_id | Нет |
| Offer | `offers` | id, venue_id, current_price, original_price, quantity_available, expires_at, status | Нет |
| OfferItem | `offer_items` | id, offer_id, product_id, quantity | Нет |
| Review | `reviews` | id, user_id, venue_id, order_id, rating, comment, images_json | deleted_at |

**Важные Заметки:**
- `venue_id` — Логическая связь с `db_venue` (без FK constraints, валидация через gRPC)
- `user_id` — Логическая связь с `db_auth` (без FK constraints, валидация через gRPC)
- `order_id` — Логическая связь с `db_order` (без FK constraints, валидация через gRPC)
- JSONB поля — `image_urls`, `characteristics_json`, `images_json`
- ENUM `offer_status` — `active`, `sold_out`, `expired`, `cancelled`

### 6.2. Pydantic Schemas

**Файл:** `src/schemas/common.py`

**Общие Схемы:**
- `PaginatedResponse[T]` — Универсальный пагинированный ответ
- `PaginationMeta` — Метаданные пагинации
- `ErrorResponse` — Стандартизированный формат ошибок
- `IdentityContext` — Контекст идентичности от Gateway

**Схемы по Доменам:**
- Category, CategoryCreate, CategoryUpdate
- Product, ProductCreate, ProductUpdate
- Offer, OfferCreate, OfferUpdate, OfferItem, OfferItemCreate
- Review, ReviewCreate, ReviewUpdate

**Требования:**
- Все схемы с явной типизацией
- Validation rules (max_length, format, enum, min/max values)
- Separate schemas for Create/Update/Response
- Config для serialization (exclude_unset, exclude_none, etc.)

---

## 7. Безопасность и Аутентификация

### 7.1. Authentication Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client     │────▶│   Gateway    │────▶│ Catalog Service│
│              │     │    (Kong)    │     │  (Python)    │
└──────────────┘     └──────────────┘     └──────────────┘
      │                    │                    │
      │ 1. JWT Token       │                    │
      │───────────────────▶│                    │
      │                    │                    │
      │                    │ 2. Validate JWT    │
      │                    │ 3. Extract Claims  │
      │                    │                    │
      │                    │ 4. Add Headers     │
      │                    │───────────────────▶│
      │                    │  X-User-ID         │
      │                    │  X-User-Role       │
      │                    │  X-Request-ID      │
      │                    │                    │
      │                    │                    │ 5. Trust Headers
      │                    │                    │ (from trusted network)
```

### 7.2. Middleware: Auth (`src/middleware/auth.py`)

**Задачи:**
- Валидация наличия обязательных identity headers
- Проверка доверенной сети (Gateway only)
- Извлечение контекста для request scope
- Блокировка прямых запросов без Gateway

**Требования:**
- Отклонять запросы без `X-User-ID`, `X-Request-ID`
- Проверять IP адрес против `GATEWAY_TRUSTED_NETWORKS`
- Логировать все auth failures
- Возвращать стандартизированные 401/403 ошибки

### 7.3. Authorization Rules

| Resource | Action | user | staff | admin |
|----------|--------|------|-------|-------|
| categories | GET (all) | ✅ | ✅ | ✅ |
| categories | CREATE | ❌ | ❌ | ✅ |
| categories | UPDATE | ❌ | ❌ | ✅ |
| categories | DELETE | ❌ | ❌ | ✅ |
| products | GET (all) | ✅ | ✅ | ✅ |
| products | CREATE | ❌ | ❌ | ✅ |
| products | UPDATE | ❌ | ❌ | ✅ |
| products | DELETE | ❌ | ❌ | ✅ |
| offers | GET (active) | ✅ | ✅ | ✅ |
| offers | GET (own venue) | ❌ | ✅ | ✅ |
| offers | CREATE | ❌ | ✅ (own venue) | ✅ |
| offers | UPDATE | ❌ | ✅ (own venue) | ✅ |
| offers | DELETE | ❌ | ✅ (own venue) | ✅ |
| reviews | GET (all) | ✅ | ✅ | ✅ |
| reviews | CREATE | ✅ (own order) | ❌ | ✅ |
| reviews | UPDATE | ✅ (own) | ❌ | ✅ |
| reviews | DELETE | ✅ (own) | ❌ | ✅ |

### 7.4. Audit Logging

**Файл:** `src/middleware/logging.py`

**Требования:**
- Логировать все mutating операции (POST/PUT/PATCH/DELETE)
- Записывать old_values и new_values для чувствительных данных
- Включать `X-User-ID`, `X-Request-ID`, `X-Forwarded-For` в каждый лог
- Структурированный JSON формат для SIEM интеграции

**Audit Log Entry:**
```json
{
   "timestamp": "2026-03-16T10:30:00Z",
   "event_type": "audit.record_updated",
   "user_id": "uuid",
   "action": "UPDATE",
   "resource_type": "Offer",
   "resource_id": "123",
   "old_values": {"current_price": "199.00", "quantity": "5"},
   "new_values": {"current_price": "149.00", "quantity": "3"},
   "ip_address": "192.168.1.100",
   "request_id": "uuid",
   "trace_id": "opentelemetry-trace-id"
}
```

---

## 8. Observability

### 8.1. Logging

**Библиотека:** structlog

**Конфигурация:**
- Development: Console output, pretty format
- Production: JSON format, stdout
- Log levels: DEBUG (dev), INFO (staging), WARNING (prod)

### 8.2. Distributed Tracing

**Стандарт:** OpenTelemetry

**Интеграция:**
- FastAPI instrumentation (auto)
- SQLAlchemy instrumentation (manual)
- RabbitMQ instrumentation (manual)
- Redis instrumentation (auto)
- gRPC instrumentation (manual)

**Exporter:** OTLP → Jaeger/Tempo

**Spans:**
- HTTP Request span (root)
- Service method span
- Repository query span
- RabbitMQ publish span
- gRPC client call span

### 8.3. Metrics

**Библиотека:** prometheus-client

**Метрики:**

| Метрика | Тип | Описание |
|--------|-----|---------|
| `http_requests_total` | Counter | Количество HTTP запросов |
| `http_request_duration_seconds` | Histogram | Латентность запросов |
| `db_query_duration_seconds` | Histogram | Время выполнения запросов к БД |
| `rabbitmq_events_published_total` | Counter | Количество опубликованных событий |
| `grpc_calls_total` | Counter | Количество gRPC вызовов |
| `active_db_connections` | Gauge | Активные соединения к БД |
| `cache_hits_total` | Counter | Cache hits |
| `cache_misses_total` | Counter | Cache misses |

**Endpoints:**
- `/metrics` — Prometheus scrape endpoint
- `/health` — Liveness probe
- `/ready` — Readiness probe

---

## 9. Обработка Ошибок

### 9.1. Error Response Format

**Файл:** `src/schemas/common.py`

```json
{
   "code": "VALIDATION_ERROR",
   "message": "Неверные данные в запросе",
   "details": [
     {"field": "current_price", "message": "Должна быть меньше original_price"}
   ],
   "timestamp": "2026-03-16T10:30:00Z",
   "request_id": "uuid",
   "trace_id": "string"
}
```

### 9.2. Error Codes

| Code | HTTP Status | Описание |
|------|-------------|----------|
| `VALIDATION_ERROR` | 400 | Ошибка валидации входных данных |
| `UNAUTHORIZED` | 401 | Требуется аутентификация |
| `FORBIDDEN` | 403 | Недостаточно прав |
| `NOT_FOUND` | 404 | Ресурс не найден |
| `CONFLICT` | 409 | Конфликт (дубликат, review exists) |
| `INTERNAL_ERROR` | 500 | Внутренняя ошибка сервера |
| `SERVICE_UNAVAILABLE` | 503 | Сервис недоступен |
| `VENUE_NOT_FOUND` | 404 | Заведение не найдено (gRPC) |
| `ORDER_NOT_FOUND` | 404 | Заказ не найден (gRPC) |

### 9.3. Global Exception Handler

**Файл:** `src/middleware/error_handler.py`

**Задачи:**
- Перехват всех необработанных исключений
- Логирование с trace_id
- Возврат стандартизированного error response
- Не раскрытие внутренней информации в production

---

## 10. Тестирование

### 10.1. Test Strategy

| Уровень | Инструмент | Coverage Target | Описание |
|--------|------------|-----------------|----------|
| Unit | pytest | 80%+ | Тестирование отдельных функций |
| Integration | pytest + TestContainers | 70%+ | Тестирование с БД, RabbitMQ |
| E2E | pytest + httpx | 60%+ | Сквозные сценарии API |
| Contract | pytest | 100% | OpenAPI spec validation |

### 10.2. Test Structure

```
src/catalog_service/tests/
├── conftest.py              # Fixtures, test config
├── unit/
│   ├── test_services/
│   ├── test_repositories/
│   └── test_utils/
├── integration/
│   ├── test_categories_api/
│   ├── test_products_api/
│   ├── test_offers_api/
│   ├── test_reviews_api/
│   └── test_events/
└── e2e/
    ├── test_offer_flow/
    ├── test_review_flow/
    └── test_category_flow/
```

### 10.3. Test Fixtures

**conftest.py:**
- `async_client` — Async HTTP client for API tests
- `db_session` — Isolated DB session per test
- `rabbitmq_mock` — Mock for RabbitMQ publisher
- `grpc_clients_mock` — Mock for Venue/Order gRPC clients
- `identity_context` — Test identity headers
- `factory_boy` — Factories для создания тестовых данных

### 10.4. CI Pipeline (`.github/workflows/ci.yml`)

**Stages:**
1. **Lint** — ruff, mypy
2. **Test** — pytest with coverage
3. **Build** — Docker image build
4. **Security** — Dependency scan (safety, pip-audit)

**Requirements:**
- Все PR требуют passing CI
- Coverage не должен уменьшаться
- Security vulnerabilities блокируют merge

---

## 11. Миграции Базы Данных

### 11.1. Alembic Configuration

**Файл:** `alembic/env.py`

**Настройки:**
- Async support для PostgreSQL
- Target metadata из `models/base.py`
- Transaction per migration

### 11.2. Migration Workflow

```bash
# Create new migration
alembic revision --autogenerate -m "add_offer_status_enum"

# Review and edit migration file
# Apply to database
alembic upgrade head

# Rollback
alembic downgrade -1
```

### 11.3. Migration Rules

- Never edit committed migration files
- Always test migrations on staging before production
- Backward compatible — не ломать существующий API
- Data migrations — отдельный тип миграций с data backup

---

## 12. Деплой и Инфраструктура

### 12.1. Docker Configuration

**Файл:** `docker/Dockerfile`

**Требования:**
- Multi-stage build (build → runtime)
- Non-root user для безопасности
- Health check endpoint
- Graceful shutdown support

**Image Layers:**
1. Python base image (slim)
2. uv install
3. Dependencies install
4. Source code copy
5. Non-root user

### 12.2. Kubernetes Deployment

**Resources:**
- Deployment (replicas: 3 min)
- Service (ClusterIP)
- HorizontalPodAutoscaler (CPU/Memory)
- PodDisruptionBudget

**Probes:**
- Liveness: `/health` (30s interval)
- Readiness: `/ready` (10s interval)
- Startup: `/health` (initial delay 30s)

### 12.3. Environment Configuration

| Environment | Replicas | Resources | Database | RabbitMQ |
|-------------|----------|-----------|----------|----------|
| Development | 1 | 256Mi/100m | Local Docker | Local Docker |
| Staging | 2 | 512Mi/250m | Managed PostgreSQL | Managed RabbitMQ |
| Production | 3+ | 1Gi/500m | Managed PostgreSQL | Managed RabbitMQ |

### 12.4. CI/CD Pipeline

**Stages:**
1. **Build** — Docker image, push to registry
2. **Test** — Run test suite on staging
3. **Deploy Staging** — Automatic on merge to main
4. **Deploy Production** — Manual approval required

**Rollback Strategy:**
- Kubernetes rollout undo
- Database migration rollback plan
- Feature flags для gradual rollout

---

## 13. Производительность и Масштабирование

### 13.1. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (P95) | ≤ 500ms | Prometheus histogram |
| Database Query Time (P95) | ≤ 100ms | SQLAlchemy logging |
| RabbitMQ Publish Latency | ≤ 50ms | Producer callback |
| gRPC Call Latency (P95) | ≤ 100ms | gRPC client metrics |
| Error Rate | ≤ 0.1% | Error logs / total requests |

### 13.2. Caching Strategy

**Redis Usage:**

| Key Pattern | TTL | Purpose |
|------------|-----|---------|
| `category:{id}` | 10min | Category cache |
| `category:tree` | 5min | Full category tree |
| `product:{id}` | 5min | Product cache |
| `offer:{id}` | 1min | Offer details (high volatility) |
| `offer:venue:{venue_id}` | 2min | Venue offers list |

**Cache Invalidation:**
- На invalidated после mutating операций
- Event-driven invalidation через RabbitMQ
- TTL-based expiration для consistency

### 13.3. Database Optimization

**Indexes (из catalog.sql):**
- Все foreign keys indexed
- Soft delete partial indexes (`WHERE deleted_at IS NULL`)
- Composite indexes для частых queries (`venue_id, status`, `expires_at`)

**Query Optimization:**
- N+1 prevention (eager loading с relationships)
- Pagination на всех list endpoints
- Connection pooling (10-20 connections)
- Read replicas для GET запросов (production)

---

## 14. gRPC Интеграции

### 14.1. Venue Service Integration

**Файл:** `src/grpc_clients/venue_client.py`

**Методы:**
| Метод | Вход | Выход | Описание |
|-------|------|-------|----------|
| `GetVenueById` | venue_id: int64 | name, address, is_open | Валидация заведения при создании оффера |
| `GetVenueCoordinates` | venue_id: int64 | latitude, longitude | Для карты в приложении |

**Требования:**
- Timeout: 5 секунд
- Retry: 3 попытки с exponential backoff
- Circuit breaker: Open после 5 failed calls

### 14.2. Order Service Integration

**Файл:** `src/grpc_clients/order_client.py`

**Методы:**
| Метод | Вход | Выход | Описание |
|-------|------|-------|----------|
| `CheckAvailability` | offer_ids: []int64 | available: bool, quantities: map | Проверка наличия |
| `ReserveItems` | offer_id, quantity | reservation_id, expires_at | Резерв на 15 минут |
| `ConfirmReservation` | reservation_id | success | Подтверждение после оплаты |
| `CancelReservation` | reservation_id | success | Отмена при неудачной оплате |
| `GetOrderById` | order_id: int64 | order details | Валидация заказа для отзыва |

**Требования:**
- Timeout: 5 секунд
- Retry: 3 попытки с exponential backoff
- Circuit breaker: Open после 5 failed calls

---

## 15. Документация

### 15.1. API Documentation

**Auto-generated:**
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

**Requirements:**
- Все endpoints documented
- Request/response examples
- Error response schemas
- Authentication requirements

### 15.2. Development Documentation

**Files:**
- `README.md` — Quick start, architecture overview
- `CONTRIBUTING.md` — Development guidelines
- `ARCHITECTURE.md` — Detailed architecture decisions
- `CHANGELOG.md` — Version history

### 15.3. Operations Documentation

**Files:**
- `RUNBOOK.md` — Incident response procedures
- `DEPLOYMENT.md` — Deployment procedures
- `MONITORING.md` — Alerting rules, dashboards

---

## 16. Чеклист Реализации

### Phase 1: Foundation (Week 1-2)
- [ ] Project structure setup
- [ ] uv + pyproject.toml configuration
- [ ] Database models (SQLAlchemy)
- [ ] Alembic migrations
- [ ] Basic FastAPI application
- [ ] Health check endpoints
- [ ] Settings management

### Phase 2: Core Features (Week 3-5)
- [ ] Category CRUD endpoints
- [ ] Product CRUD endpoints
- [ ] Offer CRUD endpoints
- [ ] Review CRUD endpoints
- [ ] Pagination implementation
- [ ] Soft delete implementation

### Phase 3: Integration (Week 6-7)
- [ ] RabbitMQ event publisher
- [ ] Gateway identity headers middleware
- [ ] gRPC Venue Service client
- [ ] gRPC Order Service client
- [ ] Structured logging
- [ ] OpenTelemetry tracing
- [ ] Prometheus metrics

### Phase 4: Quality (Week 8-9)
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] E2E tests
- [ ] Security scan
- [ ] Performance testing
- [ ] API contract validation

### Phase 5: Deployment (Week 10)
- [ ] Docker image
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline
- [ ] Staging deployment
- [ ] Production deployment
- [ ] Monitoring dashboards

---

## 17. Риски и Митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| gRPC сервисы недоступны | Средняя | Высокое | Circuit breaker, fallback caching |
| RabbitMQ queue full | Низкая | Среднее | Publisher confirms, dead letter queue |
| Database connection pool exhaustion | Средняя | Высокое | Connection pooling, monitoring alerts |
| Cache inconsistency | Средняя | Низкое | Short TTL, event-driven invalidation |
| API Gateway misconfiguration | Низкая | Высокое | Health checks, staging testing |

---

## 18. Примечания

1. **API Specification:** Отдельный файл `catalog-api-specs.yaml` содержит полную OpenAPI спецификацию. Любые изменения в API должны быть отражены там и в этой спецификации синхронно.

2. **Database Schema:** Схема БД определена в `catalog.sql`. Миграции должны соответствовать этой схеме.

3. **gRPC Contracts:** Контракты gRPC для взаимодействия с Venue и Order сервисами должны быть согласованы с командами этих сервисов.

4. **Event Schema:** События RabbitMQ должны быть документированы в отдельном файле `events.md` для потребителей событий.

5. **Security:** Все сервисы доверяют заголовкам `X-User-*` только от API Gateway. Внутренняя сеть должна быть изолирована.