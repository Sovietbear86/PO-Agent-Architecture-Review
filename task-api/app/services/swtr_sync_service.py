"""SWTR sync service for importing tasks from SberWorks Task Tracker."""
import os
import sys
import json
import subprocess
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.task import Task, Status
from app.repositories.task_repository import TaskRepository


class SWTRSyncService:
    """Service for synchronizing tasks from SberWorks Task Tracker (SWTR)."""

    def __init__(self, mcp_swtr_path: str = "/home/user/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr", api_port: int = 8003):
        self.mcp_swtr_path = mcp_swtr_path
        self.api_port = api_port
        self.token_file = os.path.expanduser("~/.config/swtr/api_key")
        self.base_url = "https://portal.works.prod.sbt/swtr"

    def _get_token(self) -> Optional[str]:
        """Read SWTR token from file."""
        try:
            with open(self.token_file, 'r') as f:
                return f.read().strip()
        except (FileNotFoundError, IOError):
            return None

    def _run_mcp_command(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run MCP command via subprocess (stdio)."""
        token = self._get_token()
        if not token:
            return None

        env = os.environ.copy()
        env['TOKEN'] = token
        env['BASE_URL'] = self.base_url
        env['PORT'] = '0'

        cmd = [
            f"{self.mcp_swtr_path}/.venv/bin/python",
            f"{self.mcp_swtr_path}/mcp_server.py"
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                cwd=self.mcp_swtr_path
            )

            # Build request - tools/call needs special handling
            if method == 'tools/call':
                request = {
                    'jsonrpc': '2.0',
                    'method': 'tools/call',
                    'params': params,
                    'id': 1
                }
            else:
                request = {
                    'jsonrpc': '2.0',
                    'method': method,
                    'params': params,
                    'id': 1
                }

            proc.stdin.write(json.dumps(request) + '\n')
            proc.stdin.flush()

            response = proc.stdout.readline()
            proc.terminate()

            return json.loads(response) if response else None
        except Exception as e:
            return None

    def _extract_text_from_json_desc(self, description: str) -> str:
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

    def _convert_swtr_to_task(self, swtr_data: Dict[str, Any]) -> Task:
        """Convert SWTR unit data to Task model."""
        # Extract summary as title
        summary = swtr_data.get('summary', '')

        # Extract assignee from attributes
        assignee = None
        for attr in swtr_data.get('attributes', []):
            if attr.get('code') == 'assigned_to':
                value = attr.get('value', {})
                assignee = f"{value.get('lastName', '')} {value.get('firstName', '')}".strip()
                if not assignee:
                    assignee = value.get('login')
                break

        # Extract and convert description
        raw_description = swtr_data.get('description', '')
        description = self._extract_text_from_json_desc(raw_description)

        # Extract SWTR workflow_status code and name
        # workflow_status can be either a string (code) or an object with code/name
        workflow_status_raw = swtr_data.get('workflow_status', {})
        
        if isinstance(workflow_status_raw, dict):
            swtr_status_code = workflow_status_raw.get('code', '')
            swtr_status_name = workflow_status_raw.get('name', '')
        else:
            # workflow_status is a string (just the code)
            swtr_status_code = str(workflow_status_raw)
            swtr_status_name = ''
        
        # Try to get status name from attributes if not in workflow_status object
        if not swtr_status_name:
            for attr in swtr_data.get('attributes', []):
                if attr.get('code') == 'workflow_status':
                    attr_value = attr.get('value', {})
                    if isinstance(attr_value, dict):
                        swtr_status_name = attr_value.get('name', '')
                        break

        # Store both the raw status code and name for accurate mapping
        # This preserves the original AS21 status for proper analytics
        source_data = {
            'swtr_code': swtr_data.get('code'),
            'swtr_summary': swtr_data.get('summary'),
            'swtr_space': swtr_data.get('space', {}).get('code'),
            'swtr_suit': swtr_data.get('suit', {}).get('code'),
            'workflow_status': swtr_status_code,
            'workflow_status_name': swtr_status_name,
            'priority': swtr_data.get('priority', {}),
            'assignee': swtr_data.get('assigned_to'),
            'responsible': swtr_data.get('responsible'),
            'reporter': swtr_data.get('reporter'),
            'deadline': swtr_data.get('deadline'),
            'created_at': swtr_data.get('createdAt'),
            'updated_at': swtr_data.get('updatedAt'),
            'swtr_attributes': swtr_data.get('attributes', []),
        }

        # Normalize SWTR status to local Status enum based on AS21 workflow
        # Using a more detailed mapping that preserves workflow_stage info
        if not swtr_status_code:
            # Default fallback
            status = Status.TODO
        elif swtr_status_code.lower() in ('closed', 'resolved'):
            status = Status.DONE
        elif swtr_status_code.lower() in ('in_progress', 'started'):
            status = Status.IN_PROGRESS
        else:
            # For other statuses (Open, Need info, Ready for review, In review, Ready for QA, QA, Reopened, Cancelled)
            # Map them to closest existing status while preserving original info in source_data
            # Open -> TODO
            # Need info -> TODO (blocked)
            # Ready for review -> IN_PROGRESS (review queue)
            # In review -> IN_PROGRESS (active review)
            # Ready for QA -> IN_PROGRESS (QA queue)
            # QA -> IN_PROGRESS (testing)
            # Reopened -> IN_PROGRESS (rework)
            # Cancelled -> TODO (but marked as cancelled in source_data)
            status = Status.TODO

        return Task(
            title=summary,
            description=description,
            assignee=assignee,
            status=status,
            source='swtr',
            source_id=swtr_data.get('code'),
            source_data=source_data,
        )

    def sync_tasks(self, space: str = "WMB", max_results: int = 100) -> Dict[str, Any]:
        """Sync tasks from SWTR to local task tracker."""
        import json

        token = self._get_token()
        if not token:
            return {'error': 'SWTR token not found. Get token from https://portal.works.prod.sbt/ssd/privileges'}

        # Find units from SWTR - use 'request' wrapper as per MCP format
        result = self._run_mcp_command(
            'tools/call',
            {
                'name': 'find_units',
                'arguments': {
                    'request': {
                        'spaces': [space],
                        'properties': {},
                        'full_info': True,
                        'page': 0,
                        'size': max_results,
                        'calculatedAttributes': [],
                        'attributes': ['code', 'summary', 'priority', 'assigned_to', 'workflow_status', 'createdAt', 'createdBy', 'updatedAt', 'updatedBy', 'space', 'suit', 'attributes']
                    }
                }
            }
        )

        if not result:
            return {'error': 'Failed to fetch units from SWTR', 'imported': 0}

        # Extract tasks from response
        tasks_data = []
        try:
            # Parse the result - it may be nested
            content = result.get('result', {}).get('content', [])
            for item in content:
                if item.get('type') == 'text':
                    try:
                        data = json.loads(item.get('text', '{}'))
                        if isinstance(data, dict):
                            # Handle both formats: direct content or wrapped in 'unit'
                            if 'unit' in data:
                                # Format: {"content": [{"unit": {...}}]}
                                tasks_data.append(data['unit'])
                            elif 'content' in data:
                                # Format: {"content": [{...}]}
                                for unit_item in data['content']:
                                    if 'unit' in unit_item:
                                        tasks_data.append(unit_item['unit'])
                            else:
                                # Format: direct object
                                tasks_data.append(data)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            return {'error': f'Failed to parse response: {str(e)}', 'imported': 0}

        if not tasks_data:
            return {'message': 'No tasks found in SWTR', 'imported': 0}

        # Convert to Task objects
        tasks = []
        for swtr_unit in tasks_data:
            task = self._convert_swtr_to_task(swtr_unit)
            tasks.append(task)

        return {
            'imported': len(tasks),
            'tasks': [task.to_dict() for task in tasks],
            'source': 'swtr',
            'space': space
        }

    def sync_single_task(self, task_code: str) -> Optional[Task]:
        """Sync a single task from SWTR by its code."""
        token = self._get_token()
        if not token:
            return None

        result = self._run_mcp_command(
            'tools/call',
            {
                'name': 'read_unit',
                'arguments': {
                    'code': task_code
                }
            }
        )

        if not result:
            return None

        try:
            content = result.get('result', {}).get('content', [])
            for item in content:
                if item.get('type') == 'text':
                    try:
                        data = json.loads(item.get('text', '{}'))
                        if isinstance(data, dict):
                            return self._convert_swtr_to_task(data)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        return None

    def get_my_tasks(self, space: str = "WMB") -> List[Dict[str, Any]]:
        """Get tasks assigned to current user from SWTR."""
        # First get all tasks
        result = self.sync_tasks(space=space, max_results=100)

        if 'error' in result:
            return []

        # Filter tasks assigned to current user
        my_tasks = []
        try:
            with open(self.token_file, 'r') as f:
                token = f.read().strip()

            # Extract user info from token (simplified)
            import base64
            parts = token.split('.')
            if len(parts) >= 2:
                try:
                    payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
                    current_user = payload.get('preferred_username', '')
                    for task in result.get('tasks', []):
                        if task.get('assignee') and current_user.lower() in task.get('assignee', '').lower():
                            my_tasks.append(task)
                except Exception:
                    pass
        except Exception:
            pass

        return my_tasks

    def sync_my_tasks(self) -> Dict[str, Any]:
        """Sync all team member tasks from SWTR using TQL filtering by assignee."""
        import sys
        import json

        # Run sync command with all spaces using system Python
        # sync_sprint_tasks.py is in the task-api directory (TQL filtering by each team member)
        script_dir = os.path.dirname(__file__)
        while os.path.basename(script_dir) != 'task-api' and script_dir != '/':
            script_dir = os.path.dirname(script_dir)
        sync_script = os.path.join(script_dir, 'sync_sprint_tasks.py')

        try:
            result = subprocess.run(
                [sys.executable, sync_script, '--space', 'WMB,OLP,DMS,CRPV', '--save'],
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                # Extract count from output and return tasks from DB
                imported = 0
                updated = 0
                for line in result.stdout.split('\n'):
                    if 'Saved' in line and 'updated' in line:
                        # Parse: "Saved 5 new tasks, updated 20 existing tasks (total: 100)"
                        import re
                        saved_match = re.search(r'Saved (\d+) new tasks', line)
                        updated_match = re.search(r'updated (\d+) existing tasks', line)
                        if saved_match:
                            imported = int(saved_match.group(1))
                        if updated_match:
                            updated = int(updated_match.group(1))
                        imported = imported + updated  # Total imported
                        break
                    elif 'Saved' in line and 'tasks' in line:
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if p == 'Saved' and i+1 < len(parts):
                                imported = int(parts[i+1])
                                break

                # Load tasks from database and return them
                from app.repositories.task_repository import TaskRepository
                repo = TaskRepository()
                tasks = repo.find_all(limit=10000)

                return {
                    'imported': imported,
                    'tasks': [task.to_dict() for task in tasks],
                    'space': 'WMB,OLP,DMS,CRPV'
                }
            else:
                return {'error': result.stderr or 'Sync failed', 'imported': 0}
        except subprocess.TimeoutExpired:
            return {'error': 'Sync timed out', 'imported': 0}
        except Exception as e:
            return {'error': str(e), 'imported': 0}

    def get_active_sprints(self, space: str = "WMB") -> Dict[str, Any]:
        """Get active sprints for a space - using MCP command."""
        result = self._run_mcp_command('tools/call', {
            'name': 'get_current_sprint',
            'arguments': {'space': space}
        })

        if not result or 'error' in result:
            return {
                "sprints": [],
                "error": result.get('error', 'Failed to get sprints') if result else 'Unknown error',
                "default": "",
                "current": ""
            }

        try:
            text_content = result['result']['content'][0]['text']
            sprint_data = json.loads(text_content)

            # Extract sprint info
            sprint_id = sprint_data.get('id', {}).get('code', '') if sprint_data.get('id') else ''
            sprint_name = sprint_data.get('name', '')

            if sprint_id:
                return {
                    "sprints": [
                        {
                            "id": sprint_id,
                            "name": sprint_name,
                            "space": space
                        }
                    ],
                    "default": sprint_id,
                    "current": sprint_id
                }
            else:
                return {"sprints": [], "default": "", "current": ""}
        except Exception as e:
            return {"sprints": [], "error": str(e), "default": "", "current": ""}

    def get_sprint_tasks(self, sprint_id: str, space: str = "WMB") -> Dict[str, Any]:
        """Get tasks from a specific sprint - using MCP command."""
        result = self._run_mcp_command('tools/call', {
            'name': 'get_sprint_tasks',
            'arguments': {'sprint_id': sprint_id}
        })

        if not result or 'error' in result:
            return {
                "tasks": [],
                "error": result.get('error', 'Failed to get sprint tasks') if result else 'Unknown error',
                "count": 0
            }

        try:
            text_content = result['result']['content'][0]['text']
            tasks_data = json.loads(text_content)

            tasks = []
            for item in tasks_data.get('content', []):
                unit = item.get('unit', {})
                task = {
                    "id": unit.get('code', ''),
                    "summary": unit.get('summary', ''),
                    "status": item.get('workflow_status', {}).get('name', ''),
                    "status_code": item.get('workflow_status', {}).get('code', ''),
                    "assignee": "",
                    "deadline": None
                }

                # Extract assignee
                for attr in item.get('attributes', []):
                    if attr.get('attribute', {}).get('code') == 'assigned_to':
                        value = attr.get('value', {})
                        if value:
                            first_name = value.get('firstName', '')
                            last_name = value.get('lastName', '')
                            task["assignee"] = f"{last_name} {first_name}".strip() if last_name else value.get('login', '')

                    if attr.get('attribute', {}).get('code') == 'deadline':
                        value = attr.get('value', '')
                        task["deadline"] = value

                tasks.append(task)

            return {
                "sprint_id": sprint_id,
                "space": space,
                "tasks": tasks,
                "count": len(tasks)
            }
        except Exception as e:
            return {"tasks": [], "error": str(e), "count": 0}

    def sync_tasks_filtered(self, assignee: str = None, sprint_id: str = None) -> Dict[str, Any]:
        """Sync tasks from SWTR with optional assignee and sprint filters.

        Uses client-side filtering: loads all tasks from TaskRepository and filters by:
        - assignee name (partial match, case-insensitive)
        - sprint_id from source_data or swtr_attributes (or 'NONE' for tasks without sprint)
        """
        repo = TaskRepository()
        tasks = repo.find_all(limit=10000)

        # Filter by assignee if provided
        if assignee:
            assignee_lower = assignee.lower()
            tasks = [t for t in tasks if t.assignee and assignee_lower in t.assignee.lower()]

        # Filter by sprint_id if provided
        if sprint_id:
            filtered_tasks = []
            for t in tasks:
                has_sprint = False
                task_sprint_id = None
                if t.source_data:
                    # Check source_data.sprint_id
                    task_sprint_id = t.source_data.get("sprint_id")
                    if not task_sprint_id:
                        # Check swtr_attributes for sprint
                        attrs = t.source_data.get('swtr_attributes', [])
                        for attr in attrs:
                            if attr.get('code') == 'scrum_board_plugin_sprint':
                                value = attr.get('value', {})
                                if isinstance(value, dict):
                                    task_sprint_id = value.get('code') or value.get('id')
                                    break
                
                # Check if sprint matches
                if task_sprint_id:
                    has_sprint = True
                    if task_sprint_id == sprint_id:
                        filtered_tasks.append(t)
                elif sprint_id == 'NONE':
                    # Task without sprint matches 'NONE' filter
                    filtered_tasks.append(t)
            tasks = filtered_tasks

        return {
            'imported': len(tasks),
            'tasks': [t.to_dict() for t in tasks],
            'source': 'swtr',
            'assignee': assignee,
            'sprint_id': sprint_id
        }
