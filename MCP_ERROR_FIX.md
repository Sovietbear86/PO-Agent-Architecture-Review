# Исправление ошибки 500 при запросе задач в спринте

## Проблема

Запросы из UI:
1. **"Покажи задачи Моисеева"** - отрабатывает успешно (200 OK)
2. **"Покажи задачи Моисеева в спринте XXX"** - падает с 500 ошибкой

## Анализ

### Структура MCP-серверов

В проекте используется два MCP-сервера:

1. **`mcp-swtr`** - FastMCP Python сервер для SWTR API
   - Расположение: `mcp-swtr/mcp_server.py`
   - Порт: 8000 (по умолчанию, определяется из env PORT)
   - Используется для прямых запросов к SWTR API

2. **`s21_mcp_server.py`** - FastAPI Python сервер для TeamPerformanceAgent
   - Расположение: `task-api/s21_agent_mcp_server.py`
   - Порт: 3001
   - Использует `TeamPerformanceAgent` с `TaskService` и `SWTRAdapter`

### Цепочка вызовов

```
UI Query -> s21_mcp_server.py:3001 -> TeamPerformanceAgent
    -> TaskService -> SWTRAdapter -> FastAPI API:8003
```

### Проблема в SWTRAdapter

В `task-api/src/s21_agent/connectors/s21_swtr_adapter.py`:

```python
def __init__(self, api_port: int | None = None) -> None:
    self.api_port = api_port or 8003  # DEFAULT PORT 8003!
```

При создании `SWTRAdapter` без явного указания порта, используется порт **8003**.

Если FastAPI сервер не запущен на порту 8003, вызов `requests.get()` выбросит исключение:

```python
response = requests.get(
    f"http://{self.api_host}:{self.api_port}/api/v1/tasks",
    params=params,
    timeout=self.timeout,
)
response.raise_for_status()  # <-- Это вызовет исключение, если сервер недоступен
```

### Почему первый запрос работает, а второй нет?

Вероятные причины:
1. **Кэширование данных**: Первый запрос может использовать данные из репозитория, второй - пытается обновить
2. **Разные пути выполнения**: Первый запрос может идти через один путь, второй - через другой
3. **Состояние сервера**: Сервер на 8003 мог быть запущен между запросами

## Решение

### Вариант 1: Проверить, запущен ли сервер на 8003

До вызова `SWTRAdapter`, проверять доступность сервера:

```python
def search_tasks(self, query: str, filters: dict[str, Any] | None = None) -> list[Task]:
    """Search tasks in SWTR."""
    import requests

    # Check if server is available before making request
    try:
        health_response = requests.get(
            f"http://{self.api_host}:{self.api_port}/health",
            timeout=5
        )
        if health_response.status_code != 200:
            print(f"Server on port {self.api_port} is not healthy")
            return []
    except Exception as e:
        print(f"Server on port {self.api_port} is not available: {e}")
        return []

    # Proceed with task search...
```

### Вариант 2: Использовать репозиторий напрямую (рекомендуется)

В `TaskService` и `SWTRAdapter`, при работе с уже синхронизированными задачами, использовать `TaskRepository` напрямую, без вызова внешнего API:

```python
class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    # Для получения уже сохраненных задач - использовать repository
    def get_tasks(self, ...):
        return self.repository.find_all(...)
```

### Вариант 3: Добавить fallback в SWTRAdapter

Если API недоступен, вернуть данные из репозитория:

```python
def search_tasks(self, query: str, filters: dict[str, Any] | None = None) -> list[Task]:
    """Search tasks in SWTR."""
    import requests
    from app.repositories.task_repository import TaskRepository

    try:
        # Try API first
        response = requests.get(...)
        response.raise_for_status()
        data = response.json()
        return [self._map_to_task(task) for task in data]
    except Exception as e:
        print(f"API error, falling back to repository: {e}")
        
        # Fallback to repository
        repository = TaskRepository()
        tasks = repository.find_all(...)
        return tasks
```

## Экстренная проверка

Проверить, запущен ли FastAPI сервер:

```bash
# Попробуйте получить health endpoint
python3 -c "import requests; print(requests.get('http://localhost:8003/health').json())"

# Или проверить процессы
ps aux | grep uvicorn
```

## Рекомендации

1. **Запустить FastAPI сервер** на порту 8003:
   ```bash
   cd task-api
   uvicorn main:app --reload --port 8003
   ```

2. **Использовать репозиторий напрямую** для получения уже сохраненных задач

3. **Добавить fallback** в `SWTRAdapter` для работы без API

4. **Логировать ошибки** лучше, чтобы было понятно, что происходит

## Дополнительные файлы

- `task-api/app/routers/tasks.py` - содержит `/api/v1/tasks/get_by_url` endpoint
- `task-api/app/repositories/task_repository.py` - singleton с file persistence
- `task-api/src/s21_team_performance/config.py` - конфигурация
- `task-api/src/s21_team_performance/skills/sprint_health.py` - основной скилл для получения задач
