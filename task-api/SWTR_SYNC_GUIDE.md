# SWTR Task Sync Guide

## Overview

The task tracker now supports synchronization with SberWorks Task Tracker (SWTR).

## Features

- **Local tasks**: Managed directly in the FastAPI server
- **SWTR tasks**: Synced from SberWorks Task Tracker
- **Source filtering**: Filter tasks by source (`source=swtr` or `source=local`)

## Setup

1. Get your SWTR token from: https://portal.works.prod.sbt/ssd/privileges
2. Save it to: `~/.config/swtr/api_key`
3. Run the FastAPI server: `cd task-api && .venv/bin/python -m uvicorn main:app --reload`

## Usage

### CLI Tool (Recommended)

Sync tasks from SWTR and save to local database:

```bash
cd task-api
.venv/bin/python swtr_sync_cli_v2.py --max-results 100 --save
```

Options:
- `--space WMB` - SWTR space (default: WMB)
- `--max-results 100` - Maximum tasks to sync (default: 100)
- `--save` - Save tasks to local database
- `--json` - Output in JSON format

### API Endpoints

#### Sync Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/swtr/sync \
  -H "Content-Type: application/json" \
  -d '{"space": "WMB", "max_results": 50}'
```

#### List SWTR Tasks
```bash
curl http://localhost:8000/api/v1/tasks?source=swtr
```

#### List Local Tasks
```bash
curl http://localhost:8000/api/v1/tasks?source=local
```

#### List All Tasks
```bash
curl http://localhost:8000/api/v1/tasks
```

### Syncing New Tasks

To sync new tasks from SWTR:
1. Run the CLI tool with `--save` flag
2. Tasks will be added to the local database in `~/.task-tracker/tasks.json`
3. New tasks will be available immediately via API

## Task Structure

Tasks from SWTR include:
- `source`: "swtr"
- `source_id`: Original SWTR code (e.g., "WMB-29890")
- `source_data`: Raw SWTR data including space, status, etc.

Local tasks have `source: null`.

## File Storage

Tasks are stored in: `~/.task-tracker/tasks.json`

This ensures data persists between server restarts.
