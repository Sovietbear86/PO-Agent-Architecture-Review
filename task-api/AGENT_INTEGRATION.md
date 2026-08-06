# Агент владельца продукта (S21 Task Agent)

## Обзор

Агент - интеллектуальный инструмент для поиска и анализа задач в SWTR, интегрированный в Task Tracker.

## Установка

1. Установите новые зависимости:
```bash
cd task-api
pip install -r requirements.txt
```

2. Запустите MCP-сервер агента (порт 3000):
```bash
# В одном терминале
.venv/bin/python s21_agent_mcp_server.py
```

3. Запустите основной API:
```bash
.venv/bin/uvicorn main:app --reload
```

4. Запустите Vite:
```bash
npm run dev
```

## Использование

### Через UI

1. Нажмите кнопку **Агент** (синяя иконка G) в верхней части страницы
2. Введите запрос на русском или английском:
   - "найди задачи с PDF вложениями"
   - "задачи в статусе в работе"
   - "поиск по фразе Apache Iceberg"
3. Нажмите "Найти" или Enter
4. Просмотрите результаты с логом выполнения

### MCP API

МCP-сервер запущен на `http://localhost:3000` с эндпоинтами:

- `POST /tasks/search` - поиск задач
- `POST /tasks/get` - получить задачу по ID
- `POST /tasks/get_by_url` - получить задачу по URL
- `POST /tasks/assess_quality` - оценить качество задачи
- `POST /tasks/find_duplicates` - найти дубли
- `POST /tasks/summarize` - суммаризировать задачу

## Архитектура

```
UI (React)
  └─ AgentButton + AgentDialog
        └─ HTTP request
              └─ MCP Server (s21_agent_mcp_server.py)
                    └─ SWTR Adapter (s21_swtr_adapter.py)
                          └─ API (localhost:8000)
```

## Структура агента

```
task-api/
├── src/s21_agent/           # Ядро агента
│   ├── __init__.py
│   ├── config.py            # Настройки
│   ├── models/              # Модели (Task, Comment, Attachment)
│   ├── services/            # Бизнес-логика
│   └── connectors/          # Адаптеры
│       └── s21_swtr_adapter.py
├── s21_agent_mcp_server.py  # MCP сервер
└── tests/
    └── unit/
        └── test_s21_agent_mcp.py
```

## Модели данных

### Task
```typescript
{
  id: string
  source_id: string        // SWTR ID (например, WMB-12345)
  title: string
  description: string
  status: "todo" | "in_progress" | "done"
  assignee?: string
  deadline?: string
  source_url?: string
  created_at: string
  updated_at: string
}
```

## Настройки

Создайте `.env` файл в `task-api`:

```env
MCP_HOST=localhost
MCP_PORT=3000
MCP_TIMEOUT_SECONDS=30
MAX_RESULTS=50
SHOW_SOURCES=true
SHOW_CONFIDENCE=true
```

## Разработка

### Unit тесты
```bash
cd task-api
pytest tests/unit/test_s21_agent_mcp.py -v
```

### Добавление новых инструментов

1. Добавьте endpoint в `s21_agent_mcp_server.py`
2. Создайте adapter method в `s21_swtr_adapter.py`
3. Добавьте unit-тест

## Ограничения

- Работает только на чтение (изменение задач не поддерживается)
- MCP-сервер должен быть запущен отдельно
- Запросы выполняются от имени текущего пользователя
