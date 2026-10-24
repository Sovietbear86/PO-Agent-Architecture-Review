# PO Agent Platform v2.1 Frontend

React + TypeScript + Vite frontend for PO Agent Platform v2.1.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on `http://localhost:5174`.

## API Integration

The frontend connects to the FastAPI backend on `http://localhost:8004` via the `/api/v1` endpoints.

## Views

- `/` - Assistant (chat interface)
- `/tasks` - Tasks list with filters
- `/sprint` - Sprint view
- `/team` - Team members and capacity
- `/releases` - Release management
- `/quality` - Evaluation results

## Development

```bash
# Type check
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```
