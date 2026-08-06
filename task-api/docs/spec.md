# SPA Specification: Task Tracker

## Overview

Лёгкое SPA-приложение для управления задачами внутри небольшой команды. Данные хранятся в localStorage — перезагрузка страницы не сбрасывает список задач.

**Стек:** React 18+, TypeScript, Vite  
**Тесты:** Vitest + React Testing Library

---

## Components

### 1. TaskItem

Компонент отображения одной задачи.

#### Props

| Параметр | Тип | Описание |
|----------|-----|----------|
| `task` | `Task` | Данные задачи |
| `onUpdate` | `(id: string, updates: Partial<Task>) => void` | Обновление задачи |
| `onDelete` | `(id: string) => void` | Удаление задачи |

#### State

Компонент может иметь локальное состояние для отображения формы редактирования.

---

### 2. TaskForm

Форма создания новой задачи.

#### Props

| Параметр | Тип | Описание |
|----------|-----|----------|
| `onSubmit` | `(task: CreateTaskInput) => void` | Обработка отправки формы |

#### State

```typescript
{
  title: string;
  description: string;
  assignee: string;
}
```

#### Validation

- `title`: обязательное поле, 1-200 символов
- `description`: опциональное, макс. 1000 символов
- `assignee`: опциональное, макс. 100 символов

---

### 3. TaskList

Список задач с фильтрацией.

#### Props

| Параметр | Тип | Описание |
|----------|-----|----------|
| `tasks` | `Task[]` | Список задач |
| `onUpdate` | `(id: string, updates: Partial<Task>) => void` | Обновление задачи |
| `onDelete` | `(id: string) => void` | Удаление задачи |

#### State

```typescript
{
  filterStatus: 'all' | 'todo' | 'in_progress' | 'done';
  filterAssignee: string;
}
```

---

### 4. FilterBar

Панель фильтрации задач.

#### Props

| Параметр | Тип | Описание |
|----------|-----|----------|
| `selectedStatus` | `'all' | 'todo' | 'in_progress' | 'done'` | Выбранный статус |
| `selectedAssignee` | `string` | Выбранный исполнитель |
| `onStatusChange` | `(status: 'all' | 'todo' | 'in_progress' | 'done') => void` | Смена фильтра по статусу |
| `onAssigneeChange` | `(assignee: string) => void` | Смена фильтра по исполнителю |
| `assignees` | `string[]` | Список уникальных исполнителей |

---

### 5. App (Root Component)

Главный компонент приложения.

#### State

```typescript
{
  tasks: Task[];
  newTaskFormOpen: boolean;
}
```

#### Actions

- `addTask(task: CreateTaskInput)` — создать новую задачу
- `updateTask(id: string, updates: Partial<Task>)` — обновить задачу
- `deleteTask(id: string)` — удалить задачу
- `loadTasks()` — загрузить задачи из localStorage
- `saveTasks()` — сохранить задачи в localStorage

---

## Data Models

### Task

```typescript
interface Task {
  id: string;                // UUID
  title: string;             // Название (обязательное, 1-200 символов)
  description: string;       // Описание (макс. 1000 символов)
  assignee: string;          // Исполнитель (макс. 100 символов)
  status: Status;            // Статус задачи
  createdAt: string;         // ISO 8601 дата создания
  updatedAt: string;         // ISO 8601 дата обновления
}

type Status = 'todo' | 'in_progress' | 'done';
```

### CreateTaskInput

```typescript
interface CreateTaskInput {
  title: string;
  description?: string;
  assignee?: string;
}
```

---

## localStorage Schema

Данные хранятся в формате JSON:

```json
{
  "tasks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Implement API endpoint",
      "description": "Create POST /api/v1/tasks",
      "assignee": "alice",
      "status": "todo",
      "createdAt": "2026-07-13T10:30:00.000Z",
      "updatedAt": "2026-07-13T10:30:00.000Z"
    }
  ]
}
```

**Ключ:** `task-tracker`

---

## User Scenarios

### 1. Создание задачи

1. Пользователь открывает приложение
2. В форме TaskForm вводит название (обязательное), описание и исполнителя
3. Нажимает кнопку "Создать"
4. Задача добавляется в список с текущим временем `createdAt` и `updatedAt`
5. Данные сохраняются в localStorage

---

### 2. Просмотр списка задач

1. Пользователь видит список задач в TaskList
2. Фильтры показывают все задачи по умолчанию
3. Каждая задача отображает: название, описание, исполнителя, статус

---

### 3. Фильтрация задач

1. Пользователь выбирает статус в FilterBar (all/todo/in_progress/done)
2. Список обновляется, показывая только задачи с выбранным статусом
3. Пользователь может ввести имя исполнителя для фильтрации
4. Фильтры применяются к локальному списку без серверных запросов

---

### 4. Обновление статуса задачи

1. Пользователь нажимает кнопку "В работу" / "Выполнено" у задачи
2. Статус задачи меняется (можно в любом порядке: `todo` → `in_progress` → `done`)
3. Обновляется `updatedAt`
4. Данные сохраняются в localStorage

---

### 5. Редактирование задачи

1. Пользователь открывает форму редактирования
2. Меняет название, описание или исполнителя
3. Нажимает "Сохранить"
4. Обновляется задача и сохраняется в localStorage

---

### 6. Удаление задачи

1. Пользователь нажимает кнопку "Удалить"
2. Задача удаляется из списка
3. Данные сохраняются в localStorage

---

### 7. Перезагрузка страницы

1. При загрузке приложения вызывается `loadTasks()`
2. Данные из localStorage загружаются в состояние
3. Список задач отображается без потери данных

---

## Interactions with localStorage

### loadTasks()

```typescript
const loadTasks = () => {
  const stored = localStorage.getItem('task-tracker');
  if (stored) {
    try {
      const data = JSON.parse(stored);
      setTasks(data.tasks || []);
    } catch (e) {
      console.error('Failed to parse localStorage data');
      setTasks([]);
    }
  }
};
```

### saveTasks()

```typescript
const saveTasks = (tasksToSave: Task[]) => {
  try {
    localStorage.setItem('task-tracker', JSON.stringify({ tasks: tasksToSave }));
  } catch (e) {
    console.error('Failed to save to localStorage', e);
  }
};
```

### Обновления

Все изменения (добавление, редактирование, удаление) немедленно синхронизируются с localStorage через `saveTasks()`.

---

## UI Layout

```
┌─────────────────────────────────────────────────────┐
│                 Task Tracker Header                 │
├─────────────────────────────────────────────────────┤
│  FilterBar: [Status ▼] [Assignee ▼]               │
├─────────────────────────────────────────────────────┤
│  TaskList:                                          │
│  ┌───────────────────────────────────────────────┐ │
│  │ TaskItem: [Title] [Assignee] [Status] [Edit] │ │
│  └───────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│  TaskForm: [Title] [Desc] [Assignee] [+ Create]   │
└─────────────────────────────────────────────────────┘
```

---

## Validation Rules

| Поле | Обязательное | Мин. длина | Макс. длина | Примечание |
|------|--------------|------------|-------------|------------|
| `title` | ✅ | 1 | 200 | Обязательное для создания |
| `description` | ❌ | 0 | 1000 | Опциональное |
| `assignee` | ❌ | 0 | 100 | Опциональное |
| `status` | — | — | — | `todo` / `in_progress` / `done` |

---

## Status Flow

```
todo → in_progress → done
     ↘───────────────┘
```

- Новая задача всегда создается с `status: 'todo'`
- Возможен переход в любом порядке
