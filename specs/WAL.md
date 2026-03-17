# WAL.md — Write-Ahead Log (состояние сессии)

Этот файл содержит текущее состояние проекта. Он обновляется AI в конце каждой сессии, а также при критических изменениях. Человек проверяет его ежедневно.

## Current Phase
<!-- Укажи активную задачу: PROP-XXX: краткое описание — статус (IN PROGRESS / BLOCKED) -->
**PROP‑001: OPROTO Message Verification — IN PROGRESS**

## Completed
<!-- Завершённые пункты (можно группировать по PROP). Каждый: ссылка на спеки + краткий итог -->
- `spec://com.example.oproto/PROP-001#transport` — реализован базовый транспорт (тесты проходят)
- `spec://com.example.oproto/PROP-001#message-format` — protobuf схемы утверждены
- `spec://com.example.oproto/PROP-001#security` — TLS настройки, проверено на тестовом стенде

## In Progress
<!-- Детали текущей работы: DONE / TODO с ссылками на спеки -->
### DONE
- `spec://com.example.oproto/PROP-001#verification.normal` — хэш-матчер (`crates/oproto-core/src/verify.rs`)
- `spec://com.example.oproto/PROP-001#verification.timeout` — базовый таймаут (600 сек), конфиг в `config.rs`
### TODO
- `spec://com.example.oproto/PROP-001#verification.degraded` — обработка деградированного режима
- `spec://com.example.oproto/PROP-001#verification.mismatch` — логика расхождения

## Known Issues
<!-- Конкретные проблемы: файл, строка, описание -->
1. **Reconnection после потери сети** — `crates/otg-core/src/telegram.rs:120`, логика не обрабатывает edge‑case.
2. **Неясная семантика `edge_url`** — protobuf поле `MediaRef.edge_url` требует уточнения.

## Decisions Pending
<!-- Вопросы к человеку, требующие решения -->
- `spec://com.example.oproto/PROP-001#verification.mismatch` — что делать, если у edge есть сообщение, которого нет в Telegram? Нужно решение: игнорировать, логировать, запрашивать подтверждение?

## Session Context
<!-- Контекст для следующей сессии: с чего начать, ключевые файлы, что не трогать -->
- **Start with**: прочитать `spec://com.example.oproto/PROP-001#verification.degraded`
- **Key files**:
  - `crates/oproto-core/src/verify.rs`
  - `crates/otg-core/src/telegram.rs`
- **Run first**: `cargo test -p oproto-core -- --nocapture`
- **Watch out**: **НЕ трогать** `match_by_hash()` — функция стабильна и покрыта тестами.

---
