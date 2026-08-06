#!/usr/bin/env python3
"""Sync all tasks from SWTR spaces (no filtering - gets all tasks from space)."""
import sys
import os
import json
import subprocess
import argparse
from datetime import datetime, timezone
from uuid import uuid4
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.models.task import Task, Status
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


def load_status_mapping():
    """Load status mapping from config file."""
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    mapping_file = os.path.join(config_dir, 'status_mapping.yaml')
    
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def start_mcp_server() -> subprocess.Popen:
    """Start the MCP server process for SWTR."""
    import subprocess
    token = os.environ.get('TOKEN')
    if not token:
        try:
            with open(os.path.expanduser('~/.config/swtr/api_key'), 'r') as f:
                token = f.read().strip()
        except:
            pass

    base_url = os.environ.get('BASE_URL', 'https://portal.works.prod.sbt/swtr')
    env = os.environ.copy()
    env['TOKEN'] = token
    env['BASE_URL'] = base_url
    env['PORT'] = '0'

    script_dir = os.path.dirname(os.path.abspath(__file__))
    while os.path.basename(script_dir) != 'task-api' and script_dir != '/':
        script_dir = os.path.dirname(script_dir)

    script_path = os.path.join(script_dir, '..', 'mcp-swtr', 'mcp_server.py')
    python_path = os.path.join(script_dir, '..', 'mcp-swtr', '.venv', 'bin', 'python')
    
    # Verify python path exists
    if not os.path.exists(python_path):
        python_path = 'python3'  # Fallback to system python

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
    print(f"DEBUG: method={method}, response_len={len(response) if response else 0}, response={response[:100] if response else 'None'}")
    return json.loads(response) if response else {'error': 'No response'}


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


def sync_all_tasks(space: str = "WMB", max_results: int = 500) -> list:
    """Sync all tasks from SWTR space (no filtering - gets all tasks from space)."""
    proc = start_mcp_server()

    try:
        # Initialize
        init_response = send_mcp_request(proc, 'initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'sync-all', 'version': '1.0'}
        })

        if 'error' in init_response:
            raise ValueError(f"Initialization failed: {init_response['error']}")

        print(f"Getting tasks from space: {space}")

        # Find units without filter (get all tasks from space)
        tasks_data = []
        page = 0
        has_next = True

        while has_next and len(tasks_data) < max_results:
            find_response = send_mcp_request(proc, 'tools/call', {
                'name': 'find_units',
                'arguments': {
                    'request': {
                        'spaces': [space],
                        'properties': {},  # No filter - get all tasks
                        'full_info': True,
                        'page': page,
                        'size': 100,
                        'calculatedAttributes': [],
                        'attributes': ['code', 'summary', 'priority', 'assigned_to', 'workflow_status', 'createdAt', 'createdBy', 'updatedAt', 'updatedBy', 'space', 'suit', 'attributes']
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
                    unit = item.get('unit', {})
                    code = unit.get('code')
                    if not code:
                        continue
                    # Get attributes from unit or item
                    item_attributes = unit.get('attributes', item.get('attributes', []))
                    tasks_data.append({'unit': unit, 'attributes': item_attributes})

        print(f"Found {len(tasks_data)} tasks from space {space}")

        # Get full data for each task using read_unit to get all attributes
        full_tasks_data = []
        for item in tasks_data:
            unit = item.get('unit', {})
            code = unit.get('code')
            if not code:
                continue

            read_response = send_mcp_request(proc, 'tools/call', {
                'name': 'read_unit',
                'arguments': {'code': code}
            })

            if 'error' not in read_response:
                try:
                    resp_content = read_response.get('result', {}).get('content', [])
                    for resp_item in resp_content:
                        if isinstance(resp_item, dict) and resp_item.get('type') == 'text':
                            data = json.loads(resp_item.get('text', '{}'))
                            if isinstance(data, dict):
                                full_tasks_data.append(data)
                except json.JSONDecodeError:
                    # Fall back to original data if read_unit fails
                    full_tasks_data.append(item)
            else:
                # Fall back to original data if read_unit fails
                full_tasks_data.append(item)

        print(f"Got full data for {len(full_tasks_data)} tasks from space {space}")

        # Convert to Task objects
        tasks = []
        for swtr_unit in full_tasks_data:
            summary = swtr_unit.get('summary', '')

            # Extract assignee from attributes
            assignee = None
            for attr in swtr_unit.get('attributes', []):
                if isinstance(attr, dict):
                    attr_code = attr.get('code')
                    if attr_code == 'assigned_to':
                        value = attr.get('value')
                        if value and isinstance(value, dict):
                            assignee = f"{value.get('lastName', '')} {value.get('firstName', '')}".strip()
                            if not assignee:
                                assignee = value.get('login')
                            break

            # Extract workflow_status from attributes
            swtr_status = ''
            swtr_status_type = ''
            for attr in swtr_unit.get('attributes', []):
                if attr.get('code') == 'workflow_status':
                    value = attr.get('value', {})
                    if isinstance(value, dict):
                        swtr_status = value.get('code', '')
                        swtr_status_type = value.get('statusType', '')
                    break

            raw_description = swtr_unit.get('description', '')
            description = extract_text_from_json_desc(raw_description)

            # Convert SWTR status to local Status using workflow_status code and mapping
            # Priority: specific code mapping -> statusType fallback -> default
            status = Status.TODO
            status_mapping = load_status_mapping()
            if status_mapping and 'status_mapping' in status_mapping:
                code_mapping = status_mapping['status_mapping']
                # Try to find by workflow_status code
                if swtr_status in code_mapping:
                    status_config = code_mapping[swtr_status]
                    status_str = status_config.get('local_status', 'todo')
                    status = Status.from_value(status_str)
                elif swtr_status_type in ['done', 'in_progress']:
                    # Fallback to statusType
                    if swtr_status_type == 'done':
                        status = Status.DONE
                    elif swtr_status_type == 'in_progress':
                        status = Status.IN_PROGRESS

            source_data = {
                'swtr_code': swtr_unit.get('code'),
                'swtr_summary': swtr_unit.get('summary'),
                'swtr_space': swtr_unit.get('space', {}).get('code'),
                'swtr_suit': swtr_unit.get('suit', {}).get('code'),
                'workflow_status': swtr_status,
                # Get workflow_status name from attributes for filtering display
                'workflow_status_name': swtr_status,  # Default to code, will be updated below
                'priority': swtr_unit.get('priority', {}),
                'assignee': swtr_unit.get('assigned_to'),
                'responsible': swtr_unit.get('responsible'),
                'reporter': swtr_unit.get('reporter'),
                'deadline': swtr_unit.get('deadline'),
                'created_at': swtr_unit.get('createdAt'),
                'updated_at': swtr_unit.get('updatedAt'),
                'swtr_attributes': swtr_unit.get('attributes', []),
            }

            # Extract workflow_status name from attributes
            for attr in swtr_unit.get('attributes', []):
                if attr.get('code') == 'workflow_status':
                    value = attr.get('value', {})
                    if isinstance(value, dict) and 'name' in value:
                        source_data['workflow_status_name'] = value['name']
                        break

            # Extract deadline from attributes if not in swtr_unit
            deadline = swtr_unit.get('deadline')
            if not deadline:
                for attr in swtr_unit.get('attributes', []):
                    if attr.get('code') == 'deadline':
                        value = attr.get('value', '')
                        if isinstance(value, str):
                            deadline = value
                        break

            # Parse deadline - convert string to datetime
            deadline_dt = None
            if deadline and isinstance(deadline, str):
                try:
                    deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    deadline_dt = None

            # Parse createdAt/updatedAt
            created_at = swtr_unit.get('createdAt')
            if created_at and isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    created_at = datetime.now(timezone.utc)

            updated_at = swtr_unit.get('updatedAt')
            if updated_at and isinstance(updated_at, str):
                try:
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    updated_at = datetime.now(timezone.utc)

            task = Task(
                id=str(uuid4()),
                title=summary,
                description=description,
                assignee=assignee,
                status=status,
                created_at=created_at,
                updated_at=updated_at,
                source='swtr',
                source_id=swtr_unit.get('code'),
                source_data=source_data,
                deadline=deadline_dt,
            )
            tasks.append(task)

        return tasks

    finally:
        proc.terminate()


def main():
    parser = argparse.ArgumentParser(description='Sync all tasks from SWTR spaces')
    parser.add_argument('--space', default='WMB', help='SWTR space(s) to sync from (comma-separated)')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum number of tasks per space')
    parser.add_argument('--save', action='store_true', help='Save to local database')
    parser.add_argument('--dry-run', action='store_true', help='Show tasks without saving')
    args = parser.parse_args()

    spaces = [s.strip() for s in args.space.split(',')]

    all_tasks = []
    for space in spaces:
        tasks = sync_all_tasks(space=space, max_results=args.max_results)
        all_tasks.extend(tasks)

    if args.dry_run:
        print(f"\nFound {len(all_tasks)} tasks from spaces {args.space}")
        for task in all_tasks[:5]:
            assignee = task.assignee or 'None'
            print(f"  - [{task.source_id}] {task.title} ({assignee})")
    else:
        print(f"\nSynced {len(all_tasks)} tasks from SWTR (spaces: {args.space})")

        if args.save:
            repo = TaskRepository()
            service = TaskService(repo)

            existing_tasks = repo.find_all()
            existing_ids = {t.source_id for t in existing_tasks if t.source_id}

            saved = 0
            for task in all_tasks:
                if task.source_id and task.source_id not in existing_ids:
                    try:
                        # Save task directly to preserve all fields including status
                        repo.save(task)
                        saved += 1
                    except Exception as e:
                        print(f"Failed to save task {task.source_id}: {e}")

            print(f"Saved {saved} new tasks to local database (total: {len(repo.find_all())})")


if __name__ == '__main__':
    main()
