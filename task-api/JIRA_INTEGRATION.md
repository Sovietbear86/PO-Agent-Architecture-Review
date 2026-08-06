# FastAPI Task Tracker with Jira Integration

## Overview

This FastAPI application provides a Task Tracker with local storage and Jira integration.

## Features

### Local Task Management
- Create, read, update, delete tasks
- Filter by status, assignee
- Pagination support
- Task status transitions (todo → in_progress → done)

### Jira Integration
- Search tasks using JQL
- Get tasks by key
- Get tasks assigned to current user
- Create new Jira tasks
- Update task status
- List available projects

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
cd task-api
pip install -r requirements.txt
```

### Environment Variables

Create a `.env.local` file in the `task-api` directory:

```bash
# Jira Configuration
JIRA_URL=https://portal.works.prod.sbt
JIRA_API_TOKEN=your_personal_access_token
JIRA_USERNAME=your_username

# Optional: PLATFORM_SESSION cookie for SSO
JIRA_PLATFORM_SESSION=your_session_cookie_value

# Local database (default: true)
USE_LOCAL_DB=true
```

## Running the Server

```bash
cd task-api
python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Server will be available at:
- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## API Endpoints

### Health Check
```
GET /health
GET /api/v1/jira/health
```

### Local Tasks
```
GET    /api/v1/tasks/          # List tasks
POST   /api/v1/tasks/          # Create task
GET    /api/v1/tasks/{id}/     # Get task
PUT    /api/v1/tasks/{id}/     # Update task
PATCH  /api/v1/tasks/{id}/status/  # Update status
DELETE /api/v1/tasks/{id}/     # Delete task
```

### Jira Tasks
```
GET    /api/v1/jira/tasks?jql=...          # Search tasks
GET    /api/v1/jira/tasks/{task_key}       # Get task
GET    /api/v1/jira/tasks/my               # Get my tasks
POST   /api/v1/jira/tasks                   # Create task
PATCH  /api/v1/jira/tasks/{task_key}/status  # Update status
GET    /api/v1/jira/projects                # List projects
```

## Authentication

### Option 1: Personal Access Token
1. Get token from https://portal.works.prod.sbt/ssd/privileges
2. Set `JIRA_API_TOKEN` in `.env.local`

### Option 2: PLATFORM_SESSION Cookie
1. Log in to Jira in browser
2. Copy PLATFORM_SESSION cookie from DevTools → Application → Cookies
3. Set `JIRA_PLATFORM_SESSION` in `.env.local`

## Testing

```bash
# Run local tests
pytest

# Test with curl
curl http://127.0.0.1:8000/health

# Test Jira
curl http://127.0.0.1:8000/api/v1/jira/health
```

## Notes

- Corporate proxies may require disabling SSL verification (already configured)
- Jira API access requires valid credentials
- Local tasks are stored in memory (singleton pattern)
- React SPA available at `task-api/src/`
