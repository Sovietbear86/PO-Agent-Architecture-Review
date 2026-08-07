#!/usr/bin/env python3
"""Sync tasks from SWTR for team members (with assignee filtering via TQL)."""
import sys
import json
import os
import subprocess
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


def load_team_members() -> list:
    """Load team members from config file."""
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    members_file = os.path.join(config_dir, 'team_members.yaml')

    if os.path.exists(members_file):
        with open(members_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('members', [])
    return []


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


def sync_sprint_tasks(team_members: list = None, spaces: list = None, max_results: int = 100) -> list:
    """Sync tasks from SWTR for specific team members using TQL filtering by assignee.
    
    Args:
        team_members: List of member dicts with 'login' field (PascalCase externalId)
        spaces: List of space codes to search (WMB, OLP, DMS, CRPV)
        max_results: Max tasks per member per space
    
    Returns:
        List of Task objects
    """
    if team_members is None:
        team_members = load_team_members()
    if spaces is None:
        spaces = ['WMB', 'OLP', 'DMS', 'CRPV', 'STS']
    
    proc = start_mcp_server()

    try:
        # Initialize
        init_response = send_mcp_request(proc, 'initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'sync-sprint', 'version': '1.0'}
        })

        if 'error' in init_response:
            raise ValueError(f"Initialization failed: {init_response['error']}")

        print(f"Syncing tasks for {len(team_members)} team members across {len(spaces)} spaces")
        print(f"Max results per member per space: {max_results}\n")

        all_tasks_data = []

        for member in team_members:
            login = member.get('login', '')
            full_name = member.get('full_name', '')
            
            if not login:
                print(f"  Skipping member without login: {member}")
                continue
            
            print(f"Processing: {full_name} ({login})")
            member_tasks = []

            for space in spaces:
                # Build TQL query: space = "SPACE" AND assigned_to = "Login"
                tql = f'space = "{space}" AND assigned_to = "{login}"'
                
                find_response = send_mcp_request(proc, 'tools/call', {
                    'name': 'find_units_by_filter',
                    'arguments': {
                        'request': {
                            'query': tql,
                            'size': max_results,
                            'page': 0,
                            'calculatedAttributes': [],
                            'attributes': ['code', 'summary', 'priority', 'assigned_to', 'workflow_status', 'createdAt', 'updatedAt', 'space', 'deadline', 'description'],
                            'timeZone': 'Europe/Moscow'
                        }
                    }
                })

                if 'error' in find_response:
                    print(f"  {space}: Error - {find_response['error']}")
                    continue

                # Extract tasks from response
                content = find_response.get('result', {}).get('content', [])
                count = 0
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        try:
                            data = json.loads(item.get('text', '{}'))
                            if isinstance(data, dict) and 'content' in data:
                                for unit_item in data['content']:
                                    if isinstance(unit_item, dict) and 'unit' in unit_item:
                                        unit = unit_item['unit']
                                        # Add member info to source data
                                        unit['_sync_member'] = login
                                        unit['_sync_space'] = space
                                        all_tasks_data.append(unit)
                                        count += 1
                        except json.JSONDecodeError:
                            continue

                member_tasks.append({'space': space, 'count': count})
                print(f"  {space}: {count} tasks")

            print(f"  Total: {sum(t['count'] for t in member_tasks)} tasks")

        print(f"\nTotal tasks found: {len(all_tasks_data)}")

        # Get full data for each task using read_unit
        print("\nFetching full data for each task...")
        full_tasks_data = []
        
        for unit in all_tasks_data:
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
                    for item in resp_content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            data = json.loads(item.get('text', '{}'))
                            if isinstance(data, dict):
                                full_tasks_data.append(data)
                except json.JSONDecodeError:
                    full_tasks_data.append(unit)
            else:
                full_tasks_data.append(unit)

        print(f"Got full data for {len(full_tasks_data)} tasks")

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

            # Extract and convert description
            raw_description = swtr_unit.get('description', '')
            description = extract_text_from_json_desc(raw_description)

            # Convert SWTR status to local Status
            status = Status.TODO
            status_mapping = load_status_mapping()
            if status_mapping and 'status_mapping' in status_mapping:
                code_mapping = status_mapping['status_mapping']
                if swtr_status in code_mapping:
                    status_config = code_mapping[swtr_status]
                    status_str = status_config.get('local_status', 'todo')
                    status = Status.from_value(status_str)
                elif swtr_status_type in ['done', 'in_progress']:
                    if swtr_status_type == 'done':
                        status = Status.DONE
                    elif swtr_status_type == 'in_progress':
                        status = Status.IN_PROGRESS

            # Extract SWTR-specific data
            # Extract sprint_id from scrum_board_plugin_sprint attribute
            sprint_id = None
            for attr in swtr_unit.get('attributes', []):
                if attr.get('code') == 'scrum_board_plugin_sprint':
                    sprint_value = attr.get('value', {})
                    if sprint_value and isinstance(sprint_value, dict):
                        sprint_id = sprint_value.get('code')
                    break

            source_data = {
                'swtr_code': swtr_unit.get('code'),
                'swtr_summary': swtr_unit.get('summary'),
                'swtr_space': swtr_unit.get('space', {}).get('code'),
                'swtr_suit': swtr_unit.get('suit', {}).get('code'),
                'workflow_status': swtr_status,
                'workflow_status_name': swtr_status,
                'priority': swtr_unit.get('priority', {}),
                'deadline': swtr_unit.get('deadline'),
                'created_at': swtr_unit.get('createdAt'),
                'updated_at': swtr_unit.get('updatedAt'),
                'swtr_attributes': swtr_unit.get('attributes', []),
                'sprint_id': sprint_id,  # Add sprint_id from scrum_board_plugin_sprint
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

            # Parse deadline
            deadline_dt = None
            if deadline and isinstance(deadline, str):
                try:
                    deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    deadline_dt = None

            # Extract Due_date from attributes (priority over deadline)
            due_date = None
            for attr in swtr_unit.get('attributes', []):
                if attr.get('code') in ['Due_date', 'due_date']:
                    value = attr.get('value', '')
                    if isinstance(value, str) and value:
                        due_date = value
                        # Update deadline if not already set
                        if not deadline_dt and due_date:
                            try:
                                deadline_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                            except (ValueError, TypeError):
                                pass
                        break

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

            # Extract additional attributes for effort calculation
            estimate_hours = None
            planned_start = None
            planned_end = None
            
            for attr in swtr_unit.get('attributes', []):
                code = attr.get('code')
                if code == 'estimate':
                    value = attr.get('value')
                    if isinstance(value, (int, float)) and value > 0:
                        estimate_hours = value
                if code == 'customfield_16701':  # planned_start
                    value = attr.get('value')
                    if isinstance(value, str):
                        planned_start = value
                if code == 'customfield_16700':  # planned_end
                    value = attr.get('value')
                    if isinstance(value, str):
                        planned_end = value

            # Add additional attributes to source_data for effort calculation
            source_data['estimate_hours'] = estimate_hours
            source_data['planned_start'] = planned_start
            source_data['planned_end'] = planned_end

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
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description='Sync tasks from SWTR for team members')
    parser.add_argument('--spaces', default='WMB,OLP,DMS,CRPV', help='SWTR spaces to sync from (comma-separated)')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum tasks per member per space')
    parser.add_argument('--save', action='store_true', help='Save to local database')
    parser.add_argument('--dry-run', action='store_true', help='Show tasks without saving')
    args = parser.parse_args()

    # Split spaces if comma-separated
    spaces = [s.strip() for s in args.spaces.split(',')]

    # Load team members
    team_members = load_team_members()
    print(f"Loaded {len(team_members)} team members from config\n")

    all_tasks = sync_sprint_tasks(team_members=team_members, spaces=spaces, max_results=args.max_results)

    if args.dry_run:
        print(f"\nFound {len(all_tasks)} tasks:")
        for task in all_tasks:
            assignee = task.assignee or 'None'
            print(f"  - [{task.source_id}] {task.title} ({assignee})")
    else:
        print(f"\nSynced {len(all_tasks)} tasks from SWTR")

        if args.save:
            repo = TaskRepository()
            service = TaskService(repo)

            existing_tasks = repo.find_all()
            existing_ids = {t.source_id: t for t in existing_tasks if t.source_id}

            saved = 0
            updated = 0
            for task in all_tasks:
                if task.source_id and task.source_id not in existing_ids:
                    try:
                        repo.save(task)
                        saved += 1
                    except Exception as e:
                        print(f"Failed to save task {task.source_id}: {e}")
                elif task.source_id and task.source_id in existing_ids:
                    # Update existing task with new data
                    try:
                        existing_task = existing_ids[task.source_id]
                        # Update fields from new task
                        existing_task.title = task.title
                        existing_task.description = task.description
                        existing_task.assignee = task.assignee
                        existing_task.status = task.status
                        existing_task.created_at = task.created_at
                        existing_task.updated_at = task.updated_at
                        existing_task.source_data = task.source_data
                        existing_task.deadline = task.deadline
                        repo.save(existing_task)
                        updated += 1
                    except Exception as e:
                        print(f"Failed to update task {task.source_id}: {e}")

            print(f"Saved {saved} new tasks, updated {updated} existing tasks (total: {len(repo.find_all())})")


if __name__ == '__main__':
    main()
