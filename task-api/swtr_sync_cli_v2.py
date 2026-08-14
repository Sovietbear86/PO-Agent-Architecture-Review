#!/usr/bin/env python3
"""CLI tool for syncing tasks from SberWorks Task Tracker (SWTR) to local task tracker."""
import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from uuid import uuid4

# Add paths
task_api_path = '/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/task-api'
mcp_swtr_path = '/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr'

sys.path.insert(0, task_api_path)


def get_token() -> str | None:
    """Get SWTR token from file."""
    token_file = os.path.expanduser('~/.config/swtr/api_key')
    try:
        with open(token_file, 'r') as f:
            return f.read().strip()
    except (FileNotFoundError, IOError):
        return None


def start_mcp_server() -> subprocess.Popen:
    """Start MCP server in stdio mode."""
    token = get_token()
    if not token:
        raise ValueError("SWTR token not found. Get token from https://portal.works.prod.sbt/ssd/privileges")

    env = os.environ.copy()
    env['TOKEN'] = token
    env['BASE_URL'] = 'https://portal.works.prod.sbt/swtr'
    env['PORT'] = '0'

    cmd = [
        f"{mcp_swtr_path}/.venv/bin/python",
        f"{mcp_swtr_path}/mcp_server.py"
    ]

    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        cwd=mcp_swtr_path
    )


def send_mcp_request(proc: subprocess.Popen, method: str, params: dict) -> dict:
    """Send MCP request and receive response."""
    import time
    
    request = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': 1
    }

    proc.stdin.write(json.dumps(request) + '\n')
    proc.stdin.flush()
    time.sleep(0.5)

    response = proc.stdout.readline()
    return json.loads(response) if response else {}


def extract_text_from_json_desc(description: str) -> str:
    """Extract readable text from SWTR JSON description (DocDB format)."""
    import json
    
    try:
        data = json.loads(description)
        if not isinstance(data, dict) or 'content' not in data:
            return description
        
        def extract_from_node(node):
            """Extract text from a single node."""
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    return node.get('text', '')
                elif 'content' in node:
                    return ''.join(extract_from_node(item) for item in node['content'])
                elif node.get('type') == 'hardBreak':
                    return '\n'
            elif isinstance(node, list):
                return ''.join(extract_from_node(item) for item in node)
            return ''
        
        # Extract text from all content nodes
        text_parts = []
        for content_item in data['content']:
            text = extract_from_node(content_item)
            if text:
                text_parts.append(text)
        
        return '\n\n'.join(text_parts).strip()
    except (json.JSONDecodeError, TypeError):
        return description


def sync_tasks_from_swtr(space: str = "WMB", max_results: int = 100) -> list:
    """Sync tasks from SWTR to local task tracker."""
    proc = start_mcp_server()

    try:
        # Initialize
        init_response = send_mcp_request(proc, 'initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'sync-cli', 'version': '1.0'}
        })

        if 'error' in init_response:
            raise ValueError(f"Initialization failed: {init_response['error']}")

        # Find units - responsible is always available in full_info mode
        find_response = send_mcp_request(proc, 'tools/call', {
            'name': 'find_units',
            'arguments': {
                'request': {
                    'spaces': [space],
                    'properties': {},
                    'full_info': True,
                    'page': 0,
                    'size': max_results,
                    'calculatedAttributes': [],
                    'attributes': ['code', 'summary', 'priority', 'responsible', 'workflow_status', 'createdAt', 'createdBy', 'updatedAt', 'updatedBy', 'space', 'suit']
                }
            }
        })

        if 'error' in find_response:
            raise ValueError(f"Failed to find units: {find_response['error']}")

        # Extract tasks from response
        tasks_data = []
        content = find_response.get('result', {}).get('content', [])
        for item in content:
            if item.get('type') == 'text':
                try:
                    data = json.loads(item.get('text', '{}'))
                    if isinstance(data, dict):
                        if 'content' in data:
                            for unit_item in data['content']:
                                if 'unit' in unit_item:
                                    tasks_data.append(unit_item['unit'])
                except json.JSONDecodeError:
                    continue

        # Convert to local task format
        tasks = []
        for swtr_unit in tasks_data:
            # Extract assignee from responsible (always available)
            assignee = None
            for attr in swtr_unit.get('attributes', []):
                # Try assigned_to first, then responsible
                if attr.get('code') in ('assigned_to', 'responsible'):
                    value = attr.get('value', {})
                    assignee = f"{value.get('lastName', '')} {value.get('firstName', '')}".strip()
                    if not assignee:
                        assignee = value.get('login')
                    break

            # Determine status
            swtr_status = swtr_unit.get('workflow_status', {}).get('code', '')
            if swtr_status in ('closed', 'resolved'):
                status = 'done'
            elif swtr_status in ('in_progress', 'started'):
                status = 'in_progress'
            else:
                status = 'todo'

            task = {
                'id': str(uuid4()),
                'title': swtr_unit.get('summary', ''),
                'description': extract_text_from_json_desc(swtr_unit.get('description', '')),
                'assignee': assignee,
                'status': status,
                'created_at': swtr_unit.get('createdAt', datetime.now(timezone.utc).isoformat()),
                'updated_at': swtr_unit.get('updatedAt', datetime.now(timezone.utc).isoformat()),
                'source': 'swtr',
                'source_id': swtr_unit.get('code'),
                'source_data': {
                    'swtr_code': swtr_unit.get('code'),
                    'swtr_space': swtr_unit.get('space', {}).get('code'),
                    'workflow_status': swtr_status,
                }
            }
            tasks.append(task)

        return tasks

    finally:
        proc.terminate()


def save_tasks_to_local_db(tasks: list) -> int:
    """Save tasks to local task tracker database."""
    from app.repositories.task_repository import TaskRepository
    from app.services.task_service import TaskService

    repo = TaskRepository()
    svc = TaskService(repo)

    imported = 0
    for task_data in tasks:
        try:
            existing = repo.find_by_source_id(task_data.get('source_id'))
            # Always create new task - update is complex with current architecture
            svc.create_task_from_dict(task_data)
            imported += 1
        except Exception as e:
            print(f"Failed to save task {task_data.get('source_id')}: {e}")

    return imported


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SWTR Task Sync CLI')
    parser.add_argument('--space', default='WMB', help='SWTR space to sync from')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum tasks to sync')
    parser.add_argument('--save', action='store_true', help='Save tasks to local database')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')

    args = parser.parse_args()

    # Check token
    if not get_token():
        print("Error: SWTR token not found!")
        print("Get token from: https://portal.works.prod.sbt/ssd/privileges")
        print("Save token to: ~/.config/swtr/api_key")
        sys.exit(1)

    try:
        # Sync tasks
        tasks = sync_tasks_from_swtr(space=args.space, max_results=args.max_results)

        if args.json:
            print(json.dumps(tasks, indent=2, ensure_ascii=False))
        else:
            print(f"Synced {len(tasks)} tasks from SWTR ({args.space})")
            for task in tasks[:5]:
                print(f"  - [{task['source_id']}] {task['title']} ({task.get('assignee', 'Unassigned')})")
            if len(tasks) > 5:
                print(f"  ... and {len(tasks) - 5} more tasks")

        # Save if requested
        if args.save:
            imported = save_tasks_to_local_db(tasks)
            print(f"Saved {imported} tasks to local database")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
