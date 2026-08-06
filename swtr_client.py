#!/usr/bin/env python3
"""
Standalone SWTR (SberWorks Task Tracker) client.
Uses personal access token for authentication.
Implements basic Jira API calls.
"""

import os
import json
import urllib.request
import urllib.error
import ssl
from datetime import datetime

# Configuration
SWTR_TOKEN = os.environ.get('SWTR_TOKEN')
if not SWTR_TOKEN:
    # Try to read from file
    try:
        with open(os.path.expanduser('~/.config/swtr/api_key'), 'r') as f:
            SWTR_TOKEN = f.read().strip()
    except:
        pass

SWTR_BASE_URL = os.environ.get('SWTR_BASE_URL', 'https://portal.works.prod.sbt/swtr')
SSL_VERIFY = os.environ.get('SWTR_TLS_INSECURE', '0') != '1'

# SSL context - always disable verification for self-signed certs
ssl_context = ssl._create_unverified_context()


def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request to SWTR API."""
    url = f"{SWTR_BASE_URL}{endpoint}"
    
    req = urllib.request.Request(url, method=method)
    
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    
    if data:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
    
    try:
        resp = urllib.request.urlopen(req, timeout=30, context=ssl_context)
        return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {
            'error': {
                'code': e.code,
                'reason': e.reason,
                'body': e.read().decode('utf-8')[:500]
            }
        }
    except Exception as e:
        return {
            'error': {
                'code': 0,
                'reason': str(e)
            }
        }


def search_tasks(jql: str = "project = WMB ORDER BY created DESC", max_results: int = 20, fields: list = None):
    """
    Search tasks using JQL query.
    
    Args:
        jql: JQL query string
        max_results: Maximum number of results
        fields: List of fields to return (default: summary, status, created, priority, assignee)
    
    Returns:
        List of matching tasks
    """
    if fields is None:
        fields = ['summary', 'status', 'created', 'priority', 'assignee', 'description', 'updated']
    
    headers = {
        'Authorization': f'Bearer {SWTR_TOKEN}',
        'x-ssd-mode': 'works',
        'Accept': 'application/json'
    }
    
    search_data = {
        'jql': jql,
        'maxResults': max_results,
        'fields': fields
    }
    
    result = make_request('POST', '/rest/api/2/search', search_data, headers)
    return result


def get_task(task_key: str):
    """
    Get a single task by its key.
    
    Args:
        task_key: Task key (e.g., WMB-29995)
    
    Returns:
        Task details
    """
    headers = {
        'Authorization': f'Bearer {SWTR_TOKEN}',
        'x-ssd-mode': 'works',
        'Accept': 'application/json'
    }
    
    result = make_request('GET', f'/rest/api/2/issue/{task_key}', None, headers)
    return result


def get_current_user():
    """
    Get current user information.
    
    Returns:
        User details
    """
    headers = {
        'Authorization': f'Bearer {SWTR_TOKEN}',
        'x-ssd-mode': 'works',
        'Accept': 'application/json'
    }
    
    result = make_request('GET', '/rest/api/2/myself', None, headers)
    return result


def print_task(task_data):
    """Pretty print task data."""
    if 'error' in task_data:
        print(f"Error: {task_data['error']}")
        return
    
    issue = task_data.get('issue', task_data)
    fields = issue.get('fields', {})
    
    print(f"Key: {issue.get('key', 'N/A')}")
    print(f"Summary: {fields.get('summary', 'N/A')}")
    print(f"Description: {fields.get('description', 'N/A') or 'N/A'}")
    print(f"Status: {fields.get('status', {}).get('name', 'N/A')}")
    print(f"Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'}")
    print(f"Priority: {fields.get('priority', {}).get('name', 'N/A') if fields.get('priority') else 'N/A'}")
    print(f"Created: {fields.get('created', 'N/A')}")
    print(f"Updated: {fields.get('updated', 'N/A')}")
    print(f"Labels: {', '.join(fields.get('labels', [])) if fields.get('labels') else 'None'}")


def print_search_results(result):
    """Pretty print search results."""
    if 'error' in result:
        print(f"Error: {result['error']}")
        return
    
    total = result.get('total', 0)
    issues = result.get('issues', [])
    
    print(f"\nFound {total} tasks:")
    print("-" * 60)
    
    for issue in issues[:10]:  # Show first 10
        key = issue.get('key', 'N/A')
        summary = issue.get('fields', {}).get('summary', 'N/A')
        status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
        print(f"{key}: {summary} [{status}]")
    
    if len(issues) > 10:
        print(f"\n... and {len(issues) - 10} more tasks")


if __name__ == "__main__":
    import sys
    
    if not SWTR_TOKEN:
        print("SWTR_TOKEN not set!")
        print("Set it as environment variable or in ~/.config/swtr/api_key")
        sys.exit(1)
    
    print("SWTR Client initialized")
    print(f"Base URL: {SWTR_BASE_URL}")
    print(f"Token length: {len(SWTR_TOKEN)}")
    
    # Test connection
    print("\nTesting connection...")
    user = get_current_user()
    if 'error' in user:
        print(f"Connection failed: {user['error']}")
    else:
        print(f"Connected as: {user.get('displayName', 'Unknown')}")
    
    # Example: Search WMB tasks
    if len(sys.argv) > 1:
        if sys.argv[1] == "search":
            jql = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "project = WMB ORDER BY created DESC"
            print(f"\nSearching: {jql}")
            result = search_tasks(jql)
            print_search_results(result)
        elif sys.argv[1] == "get":
            task_key = sys.argv[2] if len(sys.argv) > 2 else ""
            if task_key:
                print(f"\nGetting task: {task_key}")
                task = get_task(task_key)
                print_task(task)
            else:
                print("Usage: python swtr_client.py get <task_key>")
        else:
            print("Usage:")
            print("  python swtr_client.py search [jql_query]")
            print("  python swtr_client.py get <task_key>")
    else:
        # Default: show my tasks
        print("\nSearching WMB tasks...")
        result = search_tasks("project = WMB ORDER BY created DESC", 5)
        print_search_results(result)
