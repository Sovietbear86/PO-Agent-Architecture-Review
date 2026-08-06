#!/usr/bin/env python3
"""Test MCP TQL query."""
import sys
import os
import subprocess
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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

    script_dir = os.path.dirname(__file__)
    while os.path.basename(script_dir) != 'task-api' and script_dir != '/':
        script_dir = os.path.dirname(script_dir)
    
    script_path = os.path.join(script_dir, 'mcp-swtr', 'mcp_server.py')
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


def main():
    proc = start_mcp_server()

    try:
        # Get TQL properties
        response = send_mcp_request(proc, 'tools/call', {
            'name': 'get_tql_properties',
            'arguments': {}
        })
        print('TQL Properties:', json.dumps(response, indent=2))
        
        # Test find_units with space only (no filter)
        response = send_mcp_request(proc, 'tools/call', {
            'name': 'find_units',
            'arguments': {
                'request': {
                    'spaces': ['WMB'],
                    'properties': {
                        'query': 'space = "WMB"'
                    },
                    'full_info': False,
                    'page': 0,
                    'size': 10,
                    'calculatedAttributes': [],
                    'attributes': ['code', 'summary', 'assigned_to']
                }
            }
        })
        print('\nfind_units result:', json.dumps(response, indent=2)[:500])
        
    finally:
        proc.terminate()


if __name__ == '__main__':
    main()
