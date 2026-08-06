#!/usr/bin/env python3
"""CLI tool to sync tasks from SberWorks Task Tracker (SWTR)."""
import json
import subprocess
import os
import sys
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

from app.models.task import Task, Status
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


def start_mcp_server() -> subprocess.Popen:
    """Start the MCP server process."""
    token = os.environ.get('TOKEN') or ''
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


def sync_tasks_from_swtr(space: str = "WMB", max_results: int = 100) -> list:
    """Sync tasks from SWTR to local task tracker using read_unit for full data."""
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

        # Find units to get unit codes
        find_response = send_mcp_request(proc, 'tools/call', {
            'name': 'find_units',
            'arguments': {
                'request': {
                    'spaces': [space],
                    'properties': {},
                    'full_info': False,
                    'page': 0,
                    'size': max_results,
                    'calculatedAttributes': [],
                    'attributes': ['code', 'summary']
                }
            }
        })

        if 'error' in find_response:
            raise ValueError(f"Failed to find units: {find_response['error']}")

        # Extract unit codes from response (full_info=True returns unit in content items)
        unit_codes = []
        content = find_response.get('result', {}).get('content', [])
        print(f"DEBUG: find_units response content length: {len(content)}")
        for item in content:
            print(f"DEBUG: item type: {item.get('type')}")
            text = item.get('text', '')
            print(f"DEBUG: text preview: {text[:100] if text else 'empty'}...")
            if item.get('type') == 'text':
                try:
                    data = json.loads(text)
                    print(f"DEBUG: parsed data keys: {list(data.keys())}")
                    if 'content' in data:
                        print(f"DEBUG: data content length: {len(data['content'])}")
                        for unit_item in data['content']:
                            if 'unit' in unit_item:
                                code = unit_item['unit'].get('code')
                                print(f"DEBUG: found unit code: {code}")
                                if code:
                                    unit_codes.append(code)
                except json.JSONDecodeError as e:
                    print(f"DEBUG: parse error: {e}")
                    print(f"DEBUG: full text: {text[:500]}")
                    continue

        if not unit_codes:
            return []

        # Get full info for each unit with all attributes using read_unit
        tasks_data = []
        for code in unit_codes:
            read_response = send_mcp_request(proc, 'tools/call', {
                'name': 'read_unit',
                'arguments': {
                    'code': code
                }
            })

            if 'error' not in read_response:
                try:
                    resp_content = read_response.get('result', {}).get('content', [])
                    for item in resp_content:
                        if item.get('type') == 'text':
                            data = json.loads(item.get('text', '{}'))
                            if isinstance(data, dict):
                                tasks_data.append(data)
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


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description='Sync tasks from SWTR')
    parser.add_argument('--space', default='WMB', help='SWTR space to sync from')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum number of tasks')
    parser.add_argument('--save', action='store_true', help='Save to local database')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    tasks = sync_tasks_from_swtr(space=args.space, max_results=args.max_results)

    if args.json:
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
    else:
        print(f"Synced {len(tasks)} tasks from SWTR ({args.space})")
        for task in tasks:
            assignee = task['assignee'] or 'None'
            print(f"  - [{task['source_id']}] {task['title']} ({assignee})")

    if args.save:
        repo = TaskRepository()
        service = TaskService(repo)

        # Delete old SWTR tasks
        old_swtr_tasks = repo.find_all(source='swtr')
        for t in old_swtr_tasks:
            repo.delete(t.id)

        # Save new tasks
        saved = 0
        for task_data in tasks:
            try:
                task = Task(**task_data)
                service.create_task(task)
                saved += 1
            except Exception as e:
                print(f"Failed to save task {task_data.get('source_id')}: {e}")

        print(f"Saved {saved} tasks to local database")


if __name__ == '__main__':
    main()
