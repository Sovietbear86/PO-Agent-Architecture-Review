#!/usr/bin/env python3
"""Sync tasks from SWTR for team members only - version 2 with read_unit."""
import sys
import os
import subprocess
from datetime import datetime, timezone
from uuid import uuid4
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.models.task import Task, Status
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService
from s21_team_performance.agent import TeamPerformanceAgent


def start_mcp_server() -> subprocess.Popen:
    """Start the MCP server process for SWTR."""
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


def sync_team_tasks(team_members: list, space: str = "WMB", max_results: int = 500) -> list:
    """Sync tasks from SWTR for team members using find_units to get codes, then read_unit for details."""
    proc = start_mcp_server()

    try:
        # Initialize
        init_response = send_mcp_request(proc, 'initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'sync-team', 'version': '1.0'}
        })

        if 'error' in init_response:
            raise ValueError(f"Initialization failed: {init_response['error']}")

        # Build TQL query for team members
        member_names = []
        for member in team_members:
            full_name_parts = member.full_name.split()
            if len(full_name_parts) >= 2:
                surname = full_name_parts[0]
                first_name = full_name_parts[1]
                member_names.append(f"{surname} {first_name}")

        if not member_names:
            print("No team members found!")
            return []

        # Create TQL query
        members_tql = ', '.join([f'"{name}"' for name in member_names])
        tql_query = f"assigned_to IN ({members_tql}) AND space = \"{space}\""

        print(f"TQL query: {tql_query}")

        # Find units to get unit codes (without full_info - it's faster)
        find_response = send_mcp_request(proc, 'tools/call', {
            'name': 'find_units',
            'arguments': {
                'request': {
                    'spaces': [space],
                    'properties': {
                        'query': tql_query
                    },
                    'full_info': False,  # Only get codes
                    'page': 0,
                    'size': max_results,
                    'calculatedAttributes': [],
                    'attributes': ['code', 'summary']
                }
            }
        })

        if 'error' in find_response:
            raise ValueError(f"Failed to find units: {find_response['error']}")

        # Extract unit codes
        unit_codes = []
        content = find_response.get('result', {}).get('content', [])
        print(f"DEBUG: find_units response content length: {len(content)}")

        for item in content:
            if item.get('type') == 'text':
                try:
                    data = json.loads(item.get('text', '{}'))
                    if 'content' in data:
                        for unit_item in data['content']:
                            if 'unit' in unit_item:
                                code = unit_item['unit'].get('code')
                                if code:
                                    unit_codes.append(code)
                except json.JSONDecodeError:
                    continue

        print(f"Found {len(unit_codes)} unit codes")

        if not unit_codes:
            return []

        # Get full info for each unit using read_unit
        tasks_data = []
        print(f"Fetching full data for {len(unit_codes)} units...")
        for i, code in enumerate(unit_codes):
            if i % 50 == 0:
                print(f"  Progress: {i}/{len(unit_codes)}")

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

        print(f"Fetched {len(tasks_data)} complete task records")

        # Convert to Task objects
        tasks = []
        for swtr_unit in tasks_data:
            summary = swtr_unit.get('summary', '')

            # Extract assignee from attributes
            assignee = None
            for attr in swtr_unit.get('attributes', []):
                if attr.get('code') == 'assigned_to':
                    value = attr.get('value', {})
                    assignee = f"{value.get('lastName', '')} {value.get('firstName', '')}".strip()
                    if not assignee:
                        assignee = value.get('login')
                    break

            # Extract and convert description
            raw_description = swtr_unit.get('description', '')
            description = extract_text_from_json_desc(raw_description)

            # Convert SWTR status to local Status
            swtr_status = swtr_unit.get('workflow_status', {}).get('code', '')
            if swtr_status in ('closed', 'resolved'):
                status = Status.DONE
            elif swtr_status in ('in_progress', 'started'):
                status = Status.IN_PROGRESS
            else:
                status = Status.TODO

            source_data = {
                'swtr_code': swtr_unit.get('code'),
                'swtr_summary': swtr_unit.get('summary'),
                'swtr_space': swtr_unit.get('space', {}).get('code'),
                'swtr_suit': swtr_unit.get('suit', {}).get('code'),
                'workflow_status': swtr_status,
                'priority': swtr_unit.get('priority', {}),
                'assignee': swtr_unit.get('assigned_to'),
                'responsible': swtr_unit.get('responsible'),
                'reporter': swtr_unit.get('reporter'),
                'deadline': swtr_unit.get('deadline'),
                'created_at': swtr_unit.get('createdAt'),
                'updated_at': swtr_unit.get('updatedAt'),
                'swtr_attributes': swtr_unit.get('attributes', []),
            }

            task = Task(
                id=str(uuid4()),
                title=summary,
                description=description,
                assignee=assignee,
                status=status,
                created_at=swtr_unit.get('createdAt', datetime.now(timezone.utc).isoformat()),
                updated_at=swtr_unit.get('updatedAt', datetime.now(timezone.utc).isoformat()),
                source='swtr',
                source_id=swtr_unit.get('code'),
                source_data=source_data,
            )
            tasks.append(task)

        return tasks

    finally:
        proc.terminate()


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description='Sync tasks from SWTR for team members')
    parser.add_argument('--space', default='WMB', help='SWTR space to sync from (comma-separated for multiple)')
    parser.add_argument('--max-results', type=int, default=500, help='Maximum number of tasks')
    parser.add_argument('--save', action='store_true', help='Save to local database')
    parser.add_argument('--dry-run', action='store_true', help='Show tasks without saving')
    args = parser.parse_args()

    # Load team members
    team_agent = TeamPerformanceAgent()
    team_members = team_agent.load_team_members()

    print(f"Loaded {len(team_members)} team members:")
    for member in team_members:
        print(f"  - {member.full_name}")

    # Split spaces if comma-separated
    spaces = [s.strip() for s in args.space.split(',')]

    all_tasks = []
    for space in spaces:
        print(f"\nSyncing from space: {space}")
        tasks = sync_team_tasks(team_members, space=space, max_results=args.max_results)
        all_tasks.extend(tasks)

    if args.dry_run:
        print(f"\nFound {len(all_tasks)} tasks:")
        for task in all_tasks:
            assignee = task.assignee or 'None'
            print(f"  - [{task.source_id}] {task.title} ({assignee})")
    else:
        print(f"\nSynced {len(all_tasks)} tasks from SWTR (spaces: {args.space})")

        if args.save:
            repo = TaskRepository()
            service = TaskService(repo)

            # Delete old SWTR tasks for team members
            old_swtr_tasks = repo.find_all(source='swtr')
            print(f"Deleting {len(old_swtr_tasks)} old SWTR tasks...")

            for t in old_swtr_tasks:
                repo.delete(t.id)

            # Save new tasks
            saved = 0
            for task in all_tasks:
                try:
                    service.create_task(task)
                    saved += 1
                except Exception as e:
                    print(f"Failed to save task {task.source_id}: {e}")

            print(f"Saved {saved} tasks to local database")


if __name__ == '__main__':
    main()
