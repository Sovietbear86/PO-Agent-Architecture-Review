#!/usr/bin/env python3
"""CLI tool for syncing tasks from SberWorks Task Tracker (SWTR) to local task tracker."""
import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from uuid import uuid4

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.task import Task, Status
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


def get_token() -> str:
    """Get SWTR token from environment or file."""
    token = os.environ.get('TOKEN')
    if not token:
        try:
            with open(os.path.expanduser('~/.config/swtr/api_key'), 'r') as f:
                token = f.read().strip()
        except:
            pass
    return token


def start_mcp_server() -> subprocess.Popen:
    """Start the MCP server process."""
    token = get_token()
    base_url = os.environ.get('BASE_URL', 'https://portal.works.prod.sbt/swtr')
    port = os.environ.get('PORT', '0')

    env = os.environ.copy()
    env['TOKEN'] = token
    env['BASE_URL'] = base_url
    env['PORT'] = port

    script_path = os.path.join(os.path.dirname(__file__), '..', 'mcp-swtr', 'mcp_server.py')
    python_path = os.path.join(os.path.dirname(__file__), '..', 'mcp-swtr', '.venv', 'bin', 'python')

    return subprocess.Popen(
        [python_path, script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        bufsize=1
    )


def send_mcp_request(proc: subprocess.Popen, method: str, params: dict) -> dict:
    """Send MCP request and wait for response."""
    request = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': 1
    }

    proc.stdin.write(json.dumps(request) + '\n')
    proc.stdin.flush()

    response = proc.stdout.readline()
    return json.loads(response)


def extract_text_from_json_desc(description: str) -> str:
    """Extract readable text from DocDB JSON description."""
    if not description:
        return ""
    if not description.startswith('{'):
        return description

    try:
        data = json.loads(description)
        if not isinstance(data, dict) or 'content' not in data:
            return description

        text_parts = []
        for item in data.get('content', []):
            item_type = item.get('type')

            if item_type == 'paragraph':
                text = ''
                for content in item.get('content', []):
                    if content.get('type') == 'text':
                        text += content.get('text', '')
                if text:
                    text_parts.append(text)

            elif item_type == 'heading':
                text = ''
                for content in item.get('content', []):
                    if content.get('type') == 'text':
                        text += content.get('text', '')
                if text:
                    text_parts.append(f"## {text}")

            elif item_type == 'bullet_list':
                for list_item in item.get('content', []):
                    list_text = ''
                    for content in list_item.get('content', []):
                        if content.get('type') == 'text':
                            list_text += content.get('text', '')
                    if list_text:
                        text_parts.append(f"- {list_text}")

        return '\n\n'.join(text_parts).strip()
    except (json.JSONDecodeError, TypeError):
        return description


def sync_tasks_from_swtr(space: str = "WMB", max_results: int = 100, assignee_login: str | None = None, assignee_fiu: str | None = None) -> list:
    """Sync tasks from SWTR to local task tracker with pagination."""
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

        # Build TQL query for assignee if specified
        tql_query = None
        if assignee_fiu:
            # Use TQL to filter by assignee full name
            tql_query = f"assigned_to.firstName ~ \"{assignee_fiu.split()[0]}\" AND assigned_to.lastName ~ \"{assignee_fiu.split()[-1]}\""
        elif assignee_login:
            # Use TQL to filter by assignee login
            tql_query = f"assigned_to.login ~ \"{assignee_login}\""

        # Find units with full_info: True (to get unit.code, unit.summary, etc.)
        tasks_data = []
        page = 0
        has_next = True

        while has_next and len(tasks_data) < max_results:
            # Search in all spaces to find all tasks
            find_spaces = [] if space == 'all' else [space]

            # Use full_info: True to get unit info
            find_response = send_mcp_request(proc, 'tools/call', {
                'name': 'find_units',
                'arguments': {
                    'request': {
                        'spaces': find_spaces,
                        'properties': {},
                        'full_info': True,
                        'page': page,
                        'size': 100,
                        'calculatedAttributes': [],
                        'attributes': ['code', 'summary', 'assigned_to']
                    }
                }
            })

            if 'error' in find_response:
                raise ValueError(f"Failed to find units: {find_response['error']}")

            result = find_response.get('result', {})
            result_content = result.get('content', [])
            
            # Extract the actual content from the text field (MCP wraps result in text)
            content = []
            for item in result_content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    try:
                        data = json.loads(item.get('text', '{}'))
                        if isinstance(data, dict):
                            content = data.get('content', [])
                            has_next = data.get('hasNext', False)
                    except json.JSONDecodeError:
                        continue
            
            page += 1

            for item in content:
                if isinstance(item, dict):
                    # Get unit info from item (full_info: True returns unit with code)
                    unit = item.get('unit', {})
                    code = unit.get('code')

                    if not code:
                        continue

                    # Extract assignee from item attributes (not unit.attributes)
                    assignee = None
                    assignee_login_from_api = None
                    attributes = item.get('attributes', [])
                    for attr in attributes:
                        if isinstance(attr, dict):
                            attr_code = attr.get('code')
                            if not attr_code:
                                attr_code = attr.get('attribute', {}).get('code')

                            if attr_code == 'assigned_to':
                                value = attr.get('value')
                                if not value:
                                    value = attr.get('attribute_value')
                                if value and isinstance(value, dict):
                                    assignee = f"{value.get('lastName', '')} {value.get('firstName', '')}".strip()
                                    if not assignee:
                                        assignee = value.get('login')
                                    assignee_login_from_api = value.get('login')
                                    print(f"DEBUG: Found assignee for {code}: {assignee}")
                                break

                    # Filter by assignee if specified (filter on client side)
                    if assignee_login:
                        # Check if assignee login matches (use login for accurate matching)
                        if not assignee_login_from_api or assignee_login.lower() not in assignee_login_from_api.lower():
                            print(f"DEBUG: Filtered out {code} (login {assignee_login_from_api} doesn't match {assignee_login})")
                            continue

                    tasks_data.append({
                        'unit': unit,
                        'attributes': attributes,
                        'assignee': assignee,
                        'code': code,
                    })

                    # Stop if we have enough tasks
                    if len(tasks_data) >= max_results:
                        break

            if not has_next:
                break

        if not tasks_data:
            return []

        # Get full task info including workflow_status via read_unit
        full_tasks_data = []
        for task_item in tasks_data:
            # Use code from task_item (works for both full_info: True and False)
            code = task_item.get('code') or task_item.get('unit', {}).get('code')
            if not code:
                continue

            # Read full unit info
            read_response = send_mcp_request(proc, 'tools/call', {
                'name': 'read_unit',
                'arguments': {'code': code}
            })

            if 'error' not in read_response:
                try:
                    result_data = read_response.get('result')
                    if result_data and isinstance(result_data, dict):
                        resp_content = result_data.get('content')
                        if resp_content and isinstance(resp_content, list):
                            for item in resp_content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    full_unit = json.loads(item.get('text', '{}'))
                                    if isinstance(full_unit, dict):
                                        # Extract assignee from read_unit response
                                        assignee = task_item['assignee']
                                        if not assignee:
                                            # Try to get assignee from read_unit
                                            for attr in full_unit.get('attributes', []):
                                                if attr.get('code') == 'assigned_to':
                                                    value = attr.get('value')
                                                    if value and isinstance(value, dict):
                                                        assignee = f"{value.get('lastName', '')} {value.get('firstName', '')}".strip()
                                                        if not assignee:
                                                            assignee = value.get('login')
                                                        break

                                        full_tasks_data.append({
                                            'unit': full_unit,
                                            'assignee': assignee
                                        })
                except Exception:
                    # Fall back to original data if read_unit fails
                    full_tasks_data.append(task_item)
            else:
                full_tasks_data.append(task_item)

        # Convert to local task format
        tasks = []
        for task_item in full_tasks_data:
            unit = task_item['unit']
            assignee = task_item['assignee']

            # Determine status from unit data (workflow_status in attributes)
            # First try to get from attributes, then from unit
            swtr_status_name = ''
            for attr in unit.get('attributes', []):
                if attr.get('code') == 'workflow_status':
                    value = attr.get('value')
                    if value and isinstance(value, dict):
                        swtr_status_name = value.get('name', '')
                        break

            if not swtr_status_name:
                # Fallback to unit.workflow_status if available
                workflow_status = unit.get('workflow_status', {})
                if isinstance(workflow_status, dict):
                    swtr_status_name = workflow_status.get('name', '')
                elif isinstance(workflow_status, str):
                    swtr_status_name = workflow_status

            # Extract deadline from attributes
            deadline = None
            for attr in unit.get('attributes', []):
                if attr.get('code') == 'deadline':
                    value = attr.get('value')
                    if value and isinstance(value, str):
                        deadline = value
                    break

            # Map SWTR status to local Status
            # Normalize to lowercase for comparison
            status_lower = swtr_status_name.lower()
            if any(s in status_lower for s in ['closed', 'resolved', 'закрыт', 'решен']):
                status = 'done'
            elif any(s in status_lower for s in ['in_progress', 'started', 'в работе', 'начат', 'escalated', 'rev', 'review', 'code_review']):
                status = 'in_progress'
            else:
                status = 'todo'

            task = {
                'id': str(uuid4()),
                'title': unit.get('summary', ''),
                'description': extract_text_from_json_desc(unit.get('description', '')),
                'assignee': assignee,
                'deadline': deadline,
                'source_url': f"https://portal.works.prod.sbt/swtr/units/all/unit/{unit.get('code')}?space={unit.get('space', {}).get('code')}&tenant=default",
                'status': status,
                'created_at': unit.get('createdAt', datetime.now(timezone.utc).isoformat()),
                'updated_at': unit.get('updatedAt', datetime.now(timezone.utc).isoformat()),
                'source': 'swtr',
                'source_id': unit.get('code'),
                'source_data': {
                    'swtr_code': unit.get('code'),
                    'swtr_space': unit.get('space', {}).get('code'),
                    'workflow_status': swtr_status_name,
                    'deadline': deadline,
                }
            }
            tasks.append(task)

        return tasks

    finally:
        proc.terminate()


def save_tasks_to_local_db(tasks: list) -> int:
    """Save tasks to local task database (append mode)."""
    repo = TaskRepository()
    service = TaskService(repo)

    # Get all existing SWTR tasks (use large limit to get all tasks)
    existing_swtr_tasks = repo.find_all(source='swtr', limit=10000)
    existing_swtr_by_id = {t.source_id: t for t in existing_swtr_tasks}

    saved = 0
    for task_data in tasks:
        try:
            source_id = task_data.get('source_id')
            if not source_id:
                continue

            # Check if task with same source_id already exists
            existing = existing_swtr_by_id.get(source_id)
            if existing:
                # Update existing task
                repo.update(existing.id, Task(
                    id=existing.id,
                    title=task_data.get('title', ''),
                    description=task_data.get('description'),
                    assignee=task_data.get('assignee'),
                    deadline=task_data.get('deadline'),
                    source_url=task_data.get('source_url'),
                    status=Status(task_data.get('status', 'todo')),
                    source=task_data.get('source'),
                    source_id=task_data.get('source_id'),
                    source_data=task_data.get('source_data', {}),
                    created_at=existing.created_at,
                    updated_at=datetime.now(timezone.utc)
                ))
            else:
                # Create new task
                task = service.create_task_from_dict(task_data)
            saved += 1
        except Exception as e:
            print(f"Error saving task {task_data.get('source_id')}: {e}")
            continue

    return saved


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Sync tasks from SWTR')
    parser.add_argument('--space', default='all', help='SWTR space to sync from (use "all" for all spaces)')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum tasks to sync')
    parser.add_argument('--assignee', default=None, help='Filter by assignee login')
    parser.add_argument('--assignee-fiu', default=None, help='Filter by assignee full name (FIU)')
    parser.add_argument('--save', action='store_true', help='Save tasks to local database')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')

    args = parser.parse_args()

    # Check token
    if not get_token():
        print("Error: SWTR token not found!")
        print("Get token from: https://portal.works.prod.sbt/ssd/privileges")
        print("Save token to: ~/.config/swtr/api_key")
        sys.exit(1)

    # Sync tasks
    tasks = sync_tasks_from_swtr(space=args.space, max_results=args.max_results, assignee_login=args.assignee, assignee_fiu=args.assignee_fiu)

    if args.json:
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
    else:
        print(f"Synced {len(tasks)} tasks from SWTR ({args.space})")
        for task in tasks[:5]:
            assignee = task.get('assignee', 'Unassigned')
            print(f"  - [{task['source_id']}] {task['title']} ({assignee})")
        if len(tasks) > 5:
            print(f"  ... and {len(tasks) - 5} more tasks")

    # Save if requested
    if args.save:
        imported = save_tasks_to_local_db(tasks)
        print(f"Saved {imported} tasks to local database")


if __name__ == '__main__':
    main()
