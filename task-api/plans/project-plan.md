# План реализации проекта Task Tracker

## Обзор

Проект включает две реализации для управления задачами:

| Реализация | Стек | Цель |
|-----------|------|------|
| **REST API** | Python 3.11+ + FastAPI | HTTP API с автоматической документацией /docs |
| **SPA Frontend** | React 18+ + TypeScript + Vite | Интерфейс без серверной инфраструктуры |

**Тесты:** pytest (API), Vitest + RTL (SPA)

---

## Часть 1: Python/FastAPI REST API

### Шаг 1: Структура проекта
- Создать папки:
  - `app/models/` — модели данных
  - `app/services/` — бизнес-логика
  - `app/repositories/` — доступ к данным
  - `app/routers/` — эндпоинты
  - `app/schemas/` — Pydantic схемы
  - `app/exceptions/` — обработка ошибок
  - `app/config/` — конфигурация
  - `tests/` — тесты
- Создать `app/__init__.py` (пустой файл для Python пакета)
- `requirements.txt`: fastapi, uvicorn, pytest, httpx
- `main.py` — точка входа с FastAPI приложением

**Примечание:** Спецификация REST API основана на BRIEF Python, а не на `docs/spec.md` (там описана SPA спецификация)

### Шаг 2: Модели данных
- `app/models/task.py`: `Task`, `Status` (enum: todo, in_progress, done)
- `app/schemas/task.py`: `TaskCreate`, `TaskUpdate`, `TaskResponse` (Pydantic с валидацией)

### Шаг 3: Репозиторий (in-memory)
- `app/repositories/task_repository.py`:
  - `save(task)`, `find_by_id(id)`, `find_all(status, assignee, limit, offset)`
  - `update(id, task)`, `delete(id)`
  - Хранение в `dict[UUID, Task]`

### Шаг 4: Сервисный слой
- `app/services/task_service.py`:
  - `create_task()`, `get_task_by_id()`, `get_tasks()`
  - `update_task()`, `delete_task()`

### Шаг 5: Эндпоинты
- `app/routers/tasks.py` (APIRouter `/api/v1/tasks`):
  - `GET /api/v1/tasks` — список (фильтры: status, assignee, limit, offset)
  - `GET /api/v1/tasks/{id}` — получить задачу
  - `POST /api/v1/tasks` — создать задачу
  - `PUT /api/v1/tasks/{id}` — обновить задачу
  - `PATCH /api/v1/tasks/{id}/status` — обновить статус
  - `DELETE /api/v1/tasks/{id}` — удалить задачу
- `main.py`: подключение роутера и `/docs` endpoint

### Шаг 6: Обработка ошибок
- `app/exceptions/handlers.py`: глобальный обработчик исключений

### Шаг 7: Тесты
- `tests/test_repository.py`, `tests/test_service.py`, `tests/test_api.py`

**Порядок:** 1 → 2 → 3 → 4 → 5 → 6 → 7

**Критерии готовности:**
- ✅ Все тесты зелёные (`pytest`)
- ✅ Сервер стартует без ошибок (`uvicorn main:app --reload`)
- ✅ `/docs` доступен и показывает все эндпоинты

---

## Часть 2: JavaScript/React SPA

### Шаг 1: Структура проекта
- Создать папки:
  - `src/components/` — UI компоненты
  - `src/hooks/` — кастомные хуки
  - `src/types/` — TypeScript типы
  - `src/__tests__/` — тесты
- Настроить `vite.config.ts`
- Настроить `vitest.config.ts` для тестов
- Создать `tsconfig.json` с правильными настройками

### Шаг 2: Типы и интерфейсы
- `src/types/task.ts`:
  ```typescript
  interface Task {
    id: string;                // UUID строка
    title: string;
    description: string;
    assignee: string;
    status: Status;
    createdAt: string;         // ISO 8601
    updatedAt: string;         // ISO 8601
  }

  interface CreateTaskInput {
    title: string;
    description?: string;
    assignee?: string;
  }

  type Status = 'todo' | 'in_progress' | 'done';
  ```

### localStorage
- Ключ хранилища: `task-tracker`
- Формат: `{"tasks": Task[]}`

### Шаг 3: Кастомные хуки
- `src/hooks/useLocalStorage.ts`: `loadTasks()`, `saveTasks()` — управление localStorage
- `src/hooks/useTasks.ts`: `addTask()`, `updateTask()`, `deleteTask()`, `filterTasks()` — логика задач

### Шаг 4: Компоненты (порядок создания)
1. **FilterBar** — выбор статуса и исполнителя
2. **TaskForm** — форма создания/редактирования
3. **TaskItem** — отображение одной задачи
4. **TaskList** — список с фильтрацией
5. **App** — главный компонент

### Шаг 5: Тесты
- `src/__tests__/useLocalStorage.test.ts`, `src/__tests__/useTasks.test.ts`
- `src/__tests__/FilterBar.test.tsx`, `src/__tests__/TaskForm.test.tsx`
- `src/__tests__/TaskItem.test.tsx`, `src/__tests__/TaskList.test.tsx`

**Порядок:** 1 → 2 → 3 → 4 → 5

**Критерии готовности:**
- ✅ Все тесты зелёные (`npm test`)
- ✅ Приложение запускается без ошибок (`npm run dev`)
- ✅ Задачи сохраняются после перезагрузки страницы (localStorage)

---

## Порядок реализации (общий)

1. **Сначала** реализовать **Python/FastAPI REST API** (Часть 1)
   - API будет использоваться в будущем для интеграции с другими системами

2. **Затем** реализовать **JavaScript/React SPA** (Часть 2)
   - SPA может работать как standalone (localStorage) или подключаться к API
