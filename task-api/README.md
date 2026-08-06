# Task Tracker API

Task Tracker API with multiple implementations.

## Implementations

| Implementation | Language | Framework | Status |
|----------------|----------|-----------|--------|
| Python | Python 3.11+ | FastAPI | ✅ |
| Java | Java 17+ | Spring Boot 3 | ✅ |
| JavaScript | React 18+ | Vite + TypeScript | ✅ |

## JavaScript (React/TypeScript) Implementation

Single Page Application (SPA) for managing tasks inside a small team.

### Features

- Create, read, update, and delete tasks
- Task status management (todo, in_progress, done)
- Filter tasks by status and assignee
- Tasks persist in browser localStorage
- Modern, responsive UI with React 18+

### Requirements

- Node.js 18+
- npm 9+

### Installation

```bash
cd task-api
npm install
```

### Running the Development Server

```bash
npm run dev
```

The application will open in your browser at `http://localhost:5173`.

### Running Tests

```bash
npm test -- --run
```

### Data Persistence

Tasks are stored in browser `localStorage` with the key `task-tracker`. Data persists across page reloads and browser restarts.

### Project Structure

```
task-api/
├── src/
│   ├── components/
│   │   ├── App.tsx
│   │   ├── FilterBar.tsx
│   │   ├── TaskForm.tsx
│   │   ├── TaskItem.tsx
│   │   └── TaskList.tsx
│   ├── hooks/
│   │   ├── useLocalStorage.ts
│   │   └── useTasks.ts
│   ├── types/
│   │   └── task.ts
│   └── __tests__/
│       ├── App.test.tsx
│       ├── FilterBar.test.tsx
│       ├── TaskForm.test.tsx
│       ├── TaskItem.test.tsx
│       ├── TaskList.test.tsx
│       ├── localStorage.test.ts
│       ├── taskOperations.test.ts
│       ├── useLocalStorage.test.ts
│       └── useTasks.test.ts
├── index.html
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Java (Spring Boot) Implementation

See [Java](#java-spring-boot-implementation) section above.
