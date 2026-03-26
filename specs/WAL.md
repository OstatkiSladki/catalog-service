# WAL.md — Write-Ahead Log (состояние сессии)

Этот файл содержит текущее состояние проекта. Он обновляется AI в конце каждой сессии, а также при критических изменениях. Человек проверяет его ежедневно.

## Current Phase
**PROP-001: Catalog Foundation Bootstrap — IN PROGRESS**

## Completed
- `spec://com.ostatki.catalog/PROP-001#foundation` — инициализирован базовый FastAPI каркас (`/api/v1`, `/health`, `/ready`), settings и middleware skeleton.
- `spec://com.ostatki.catalog/PROP-001#models` — реализованы SQLAlchemy модели по `catalog.sql` + Alembic baseline migration (`20260318_0001`).
- `spec://com.ostatki.catalog/PROP-001#repositories` — реализованы BaseRepository + доменные repositories (categories/products/offers/reviews).
- `spec://com.ostatki.catalog/PROP-001#services` — добавлены service skeleton классы с thin orchestration и TODO-маркерами для следующего инкремента.
- `spec://com.ostatki.catalog/PROP-001#quality` — зеленые проверки: `ruff`, `mypy`, `pytest`.

## In Progress
### DONE
- `spec://com.ostatki.catalog/PROP-001#foundation.structure` — создана структура каталогов и модулей.
- `spec://com.ostatki.catalog/PROP-001#foundation.settings` — централизованные настройки и `.env.example`.
- `spec://com.ostatki.catalog/PROP-001#foundation.db` — async DB session manager и readiness healthcheck.
- `spec://com.ostatki.catalog/PROP-001#api.crud.categories` — реализованы Category CRUD endpoints + admin auth + tests.
- `spec://com.ostatki.catalog/PROP-001#api.crud.products` — реализованы Product CRUD endpoints + admin auth.
- `spec://com.ostatki.catalog/PROP-001#api.crud.offers` — реализованы Offer CRUD endpoints + staff/admin auth.
- `spec://com.ostatki.catalog/PROP-001#api.crud.reviews` — реализованы Review CRUD endpoints + author/admin auth.

### TODO
- `spec://com.ostatki.catalog/PROP-001#business.rules` — включить authz/gRPC validations/event publishing.

## Known Issues
1. **Alembic env sync mode** — `alembic/env.py` пока использует синхронный `engine_from_config`; для полноценного async migration flow можно перевести на async engine later.
2. **Service layer returns** — сервисы пока intentionally thin и используют generic return typing (`Any`) до ввода доменных DTO/response schemas.

## Decisions Pending
- Нет блокирующих решений на текущий момент.

## Session Context
- **Start with**: `spec://com.ostatki.catalog/PROP-001#business.rules`
- **Key files**:
  - `src/app.py`
  - `src/api/routes/categories.py`
  - `src/models/`
  - `src/repositories/`
  - `alembic/versions/20260318_0001_catalog_baseline.py`
- **Run first**: `.venv/bin/ruff check . && .venv/bin/mypy src tests && .venv/bin/pytest -q`
- **Watch out**: при расширении сервисов не дублировать бизнес-валидацию в API layer; держать её в service layer.

---
