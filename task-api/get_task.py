#!/usr/bin/env python3
"""Get full task data from SWTR."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def start_mcp_server():
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
    python_path = '/usr/bin/python3'

    return subprocess.Popen(
        [python_path, script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        bufsize=1
    )


def send_mcp_request(proc, method, params):
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


def get_task(code: str):
    """Get full task data from SWTR."""
    proc = start_mcp_server()

    try:
        # Read unit
        response = send_mcp_request(proc, 'tools/call', {
            'name': 'read_unit',
            'arguments': {'code': code}
        })

        if 'error' in response:
            print(f"Error: {response['error']}")
            return

        result = response.get('result', {})
        content = result.get('content', [])

        for item in content:
            if item.get('type') == 'text':
                data = json.loads(item.get('text', '{}'))
                print(f"Task: {data.get('code')}")
                print(f"Summary: {data.get('summary')}")
                print(f"Assignee: {data.get('assigned_to')}")
                
                # Print all attributes
                print(f"\nAttributes ({len(data.get('attributes', []))}):")
                for attr in data.get('attributes', []):
                    print(f"  {json.dumps(attr)}")
                
                # Check for user_login
                print(f"\nChecking for user_login:")
                for attr in data.get('attributes', []):
                    if attr.get('code') in ('assigned_to', 'responsible', 'reporter'):
                        value = attr.get('value', {})
                        if isinstance(value, dict):
                            login = value.get('login', '')
                            if 'user_login' in login.lower():
                                print(f"  FOUND in {attr['code']}: {login}")

    finally:
        proc.terminate()


if __name__ == '__main__':
    get_task('WMB-29995')
