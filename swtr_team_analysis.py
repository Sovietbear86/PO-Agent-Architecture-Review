#!/usr/bin/env python3
"""
SWTR Team Task Analysis Script
Extracts full attributes and metrics from team tasks

This script:
1. Connects to SWTR API to fetch team tasks
2. Extracts all attribute values and their types
3. Generates statistics for priorities, statuses, assignees, sprints, deadlines
4. Produces a detailed report with attribute samples
"""

import json
import httpx
import asyncio
import sys
import os
from datetime import datetime
from collections import defaultdict
from typing import Any

# Load token from file
token_file = os.path.expanduser("~/.config/swtr/api_key")
with open(token_file, 'r', encoding='utf-8') as f:
    token = f.read().strip()

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Cookie': 'api_swtr_as21=true'
}

BASE_URL = "https://portal.works.prod.sbt/swtr"


async def fetch_all_tasks():
    """Fetch all tasks from multiple spaces"""
    all_tasks = []
    
    # Try TQL query to get all tasks
    tql_query = 'space IN ("DMS", "OLP", "WMB")'
    
    payload = {
        "calculatedAttributes": [],
        "attributes": [],
        "query": tql_query,
        "page": {
            "page": 0,
            "size": 200
        }
    }
    
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        response = await client.post(
            f'{BASE_URL}/rest/api/unit/v3/find/tql',
            json=payload,
            headers=headers
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error fetching tasks: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return []
        
        data = response.json()
        print(f"Total content items: {len(data.get('content', []))}")
        
        # Get full info for each task
        content = data.get('content', [])
        
        for item in content:
            if isinstance(item, dict) and 'unit' in item:
                task_code = item['unit'].get('code', '')
                if task_code:
                    try:
                        full_response = await client.get(
                            f'{BASE_URL}/rest/api/unit/v2/{task_code}',
                            headers=headers
                        )
                        if full_response.status_code == 200:
                            all_tasks.append(full_response.json())
                        else:
                            all_tasks.append(item)
                    except Exception as e:
                        print(f"Error fetching {task_code}: {e}")
                        all_tasks.append(item)
        
        print(f"Fetched {len(all_tasks)} tasks")
        return all_tasks


def get_attribute_type(value: Any) -> str:
    """Determine the type of an attribute value"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return f"list[{len(value)}]"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def extract_attributes_from_list(attr_list: list) -> dict:
    """Extract attributes from the list format and return a flattened dict"""
    attributes = {}
    for attr in attr_list:
        if isinstance(attr, dict):
            code = attr.get('code', '')
            value = attr.get('value')
            name = attr.get('name', '')
            attr_type = attr.get('type', '')
            value_as_string = attr.get('valueAsString', '')
            parameters = attr.get('parameters', {})
            
            if code:
                # Store the raw value
                attributes[code] = value
                
                # Store name
                attributes[f'{code}_name'] = name
                
                # Store type
                attributes[f'{code}_type'] = attr_type
                
                # Store valueAsString
                attributes[f'{code}_valueAsString'] = value_as_string
                
                # Store parameters
                if parameters:
                    attributes[f'{code}_params'] = parameters
                
                # Extract user info if it's a user type
                if value and isinstance(value, dict):
                    first_name = value.get('firstName', '')
                    last_name = value.get('lastName', '')
                    middle_name = value.get('middleName', '')
                    login = value.get('login', '')
                    external_id = value.get('externalId', '')
                    
                    if first_name and last_name:
                        attributes[f'{code}_full_name'] = f"{last_name} {first_name} {middle_name}".strip()
                    elif login:
                        attributes[f'{code}_full_name'] = login
                    elif external_id:
                        attributes[f'{code}_full_name'] = external_id
                    
                    # Store user fields separately
                    for user_field in ['firstName', 'lastName', 'middleName', 'login', 'externalId']:
                        if value.get(user_field):
                            attributes[f'{code}_{user_field}'] = value[user_field]
                
                # Store dict values for status, priority, etc.
                if value and isinstance(value, dict) and 'name' in value and 'code' in value:
                    attributes[f'{code}_name_value'] = value['name']
                    attributes[f'{code}_code_value'] = value['code']
    
    return attributes


def analyze_all_tasks(tasks: list) -> dict:
    """Analyze all tasks and generate statistics"""
    analysis = {
        'total_tasks': len(tasks),
        'tasks_by_space': defaultdict(int),
        'tasks_by_status': defaultdict(int),
        'tasks_by_priority': defaultdict(int),
        'tasks_by_assignee': defaultdict(int),
        'tasks_by_sprint': defaultdict(int),
        'tasks_with_deadline': 0,
        'tasks_without_deadline': 0,
        'tasks_with_attachments': 0,
        'tasks_with_comments': 0,
        'all_attributes': {},
        'attribute_samples': {},
        'attribute_types': {},
        'attribute_full_info': {},  # Full info about each attribute
    }
    
    for task in tasks:
        if not isinstance(task, dict):
            continue
            
        # Extract space
        space_raw = task.get('space', {})
        if isinstance(space_raw, dict):
            space = space_raw.get('code', str(space_raw))
        else:
            space = str(space_raw) if space_raw else 'unknown'
        analysis['tasks_by_space'][space] += 1
        
        # Extract attributes list
        attr_list = task.get('attributes', [])
        attributes = extract_attributes_from_list(attr_list)
        
        # Count by status
        workflow_status = attributes.get('workflow_status', {})
        if isinstance(workflow_status, dict):
            status_value = workflow_status.get('name', workflow_status.get('code', 'unknown'))
        else:
            status_value = str(workflow_status) if workflow_status else 'unknown'
        analysis['tasks_by_status'][status_value] += 1
        
        # Count by priority
        priority = attributes.get('priority', {})
        if isinstance(priority, dict):
            priority_value = priority.get('name', priority.get('code', 'unknown'))
        else:
            priority_value = str(priority) if priority else 'unknown'
        analysis['tasks_by_priority'][priority_value] += 1
        
        # Count by assignee
        assigned_to = attributes.get('assigned_to', {})
        if isinstance(assigned_to, dict):
            assignee_name = attributes.get('assigned_to_full_name', 'unassigned')
        else:
            assignee_name = 'unassigned'
        analysis['tasks_by_assignee'][assignee_name] += 1
        
        # Count by sprint
        sprint = attributes.get('scrum_board_plugin_sprint', {})
        if isinstance(sprint, dict):
            sprint_value = sprint.get('name', sprint.get('code', 'no_sprint'))
        elif sprint:
            sprint_value = str(sprint)
        else:
            sprint_value = 'no_sprint'
        analysis['tasks_by_sprint'][sprint_value] += 1
        
        # Deadline analysis
        deadline = attributes.get('deadline')
        if deadline:
            analysis['tasks_with_deadline'] += 1
        else:
            analysis['tasks_without_deadline'] += 1
        
        # Attachments and comments
        attachment = attributes.get('attachment', [])
        worklog = attributes.get('worklog', [])
        if attachment or worklog:
            analysis['tasks_with_attachments'] += 1
        comment = attributes.get('comment', [])
        if comment:
            analysis['tasks_with_comments'] += 1
        
        # Collect all attributes with full info
        for attr_name, attr_value in attributes.items():
            if attr_name not in analysis['all_attributes']:
                analysis['all_attributes'][attr_name] = []
                analysis['attribute_samples'][attr_name] = None
                analysis['attribute_types'][attr_name] = "unknown"
                analysis['attribute_full_info'][attr_name] = {
                    'count': 0,
                    'null_count': 0,
                    'samples': [],
                    'unique_values': set()
                }
            
            analysis['all_attributes'][attr_name].append(attr_value)
            analysis['attribute_full_info'][attr_name]['count'] += 1
            
            # Store first sample
            if analysis['attribute_samples'][attr_name] is None and attr_value is not None:
                analysis['attribute_samples'][attr_name] = attr_value
            
            # Track unique values
            if attr_value is not None:
                # Convert to hashable type for set
                if isinstance(attr_value, (list, dict)):
                    val_str = json.dumps(attr_value, ensure_ascii=False, default=str)[:200]
                else:
                    val_str = str(attr_value)[:200]
                analysis['attribute_full_info'][attr_name]['unique_values'].add(val_str)
                analysis['attribute_full_info'][attr_name]['samples'].append(attr_value)
            else:
                analysis['attribute_full_info'][attr_name]['null_count'] += 1
            
            # Update type if not null
            if attr_value is not None:
                attr_type = get_attribute_type(attr_value)
                analysis['attribute_types'][attr_name] = attr_type
    
    # Convert defaultdicts to regular dicts for JSON serialization
    analysis['tasks_by_space'] = dict(analysis['tasks_by_space'])
    analysis['tasks_by_status'] = dict(analysis['tasks_by_status'])
    analysis['tasks_by_priority'] = dict(analysis['tasks_by_priority'])
    analysis['tasks_by_assignee'] = dict(analysis['tasks_by_assignee'])
    analysis['tasks_by_sprint'] = dict(analysis['tasks_by_sprint'])
    
    return analysis


def generate_report(analysis: dict) -> str:
    """Generate a comprehensive report"""
    report = []
    report.append("=" * 80)
    report.append("SWTR TEAM TASK ANALYSIS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")
    
    # Overall statistics
    report.append("## OVERALL STATISTICS")
    report.append("-" * 40)
    report.append(f"Total tasks in database: {analysis['total_tasks']}")
    report.append("")
    
    # Tasks by space
    report.append("## TASKS BY SPACE")
    report.append("-" * 40)
    for space, count in sorted(analysis['tasks_by_space'].items(), key=lambda x: -x[1]):
        report.append(f"  {space}: {count} tasks")
    report.append("")
    
    # Tasks by status
    report.append("## TASKS BY STATUS (workflow_status)")
    report.append("-" * 40)
    for status, count in sorted(analysis['tasks_by_status'].items(), key=lambda x: -x[1]):
        report.append(f"  {status}: {count} tasks")
    report.append("")
    
    # Tasks by priority
    report.append("## TASKS BY PRIORITY")
    report.append("-" * 40)
    for priority, count in sorted(analysis['tasks_by_priority'].items(), key=lambda x: -x[1]):
        report.append(f"  {priority}: {count} tasks")
    report.append("")
    
    # Tasks by assignee
    report.append("## TASKS BY ASSIGNEE")
    report.append("-" * 40)
    for assignee, count in sorted(analysis['tasks_by_assignee'].items(), key=lambda x: -x[1]):
        report.append(f"  {assignee}: {count} tasks")
    report.append("")
    
    # Tasks by sprint
    report.append("## TASKS BY SPRINT")
    report.append("-" * 40)
    for sprint, count in sorted(analysis['tasks_by_sprint'].items(), key=lambda x: -x[1]):
        report.append(f"  {sprint}: {count} tasks")
    report.append("")
    
    # Deadline statistics
    report.append("## DEADLINE STATISTICS")
    report.append("-" * 40)
    report.append(f"  Tasks with deadline: {analysis['tasks_with_deadline']}")
    report.append(f"  Tasks without deadline: {analysis['tasks_without_deadline']}")
    report.append(f"  Deadline coverage: {analysis['tasks_with_deadline']/analysis['total_tasks']*100:.1f}%")
    report.append("")
    
    # Attachment statistics
    report.append("## ATTACHMENT & COMMENT STATISTICS")
    report.append("-" * 40)
    report.append(f"  Tasks with attachments/worklogs: {analysis['tasks_with_attachments']}")
    report.append(f"  Tasks with comments: {analysis['tasks_with_comments']}")
    report.append("")
    
    # Attribute analysis - summarize by category
    report.append("## ATTRIBUTE CATEGORIES SUMMARY")
    report.append("-" * 40)
    categories = defaultdict(lambda: {'count': 0, 'attributes': []})
    for attr_name in analysis['all_attributes'].keys():
        # Extract base attribute name (remove _name, _type, _valueAsString suffixes)
        base_name = attr_name.replace('_name', '').replace('_type', '').replace('_valueAsString', '').replace('_params', '').replace('_full_name', '').replace('_firstName', '').replace('_lastName', '').replace('_middleName', '').replace('_login', '').replace('_externalId', '').replace('_code_value', '').replace('_name_value', '')
        categories[base_name]['count'] += 1
        if attr_name not in categories[base_name]['attributes']:
            categories[base_name]['attributes'].append(attr_name)
    
    for cat_name in sorted(categories.keys()):
        cat_info = categories[cat_name]
        if cat_name:  # Skip empty
            attr_type = analysis['attribute_types'].get(cat_name, 'unknown')
            total = cat_info['count']
            report.append(f"  **{cat_name}** (type: {attr_type}): {total} variants")
    report.append("")
    
    # Full attribute analysis
    report.append("## COMPLETE ATTRIBUTE ANALYSIS")
    report.append("-" * 40)
    report.append("")
    
    for attr_name in sorted(analysis['all_attributes'].keys()):
        attr_info = analysis['attribute_full_info'].get(attr_name, {})
        values = analysis['all_attributes'][attr_name]
        null_count = attr_info.get('null_count', 0)
        total = len(values)
        non_null = total - null_count
        sample = analysis['attribute_samples'].get(attr_name, 'N/A')
        attr_type = analysis['attribute_types'].get(attr_name, 'unknown')
        
        # Skip metadata attributes (those ending with _name, _type, etc.) for the main list
        if attr_name.endswith(('_name', '_type', '_valueAsString', '_params', '_full_name')):
            continue
        
        report.append(f"### {attr_name}")
        report.append(f"  - **Type**: {attr_type}")
        report.append(f"  - **Total values**: {total}")
        report.append(f"  - **Non-null values**: {non_null}")
        report.append(f"  - **Null values**: {null_count}")
        report.append(f"  - **Coverage**: {non_null/total*100:.1f}%")
        
        # Get the base type from _type attribute
        type_attr = analysis['all_attributes'].get(f'{attr_name}_type', [])
        if type_attr:
            unique_types = set(type_attr)
            report.append(f"  - **Attribute type(s)**: {', '.join(unique_types)}")
        
        # Unique values
        if attr_info.get('unique_values'):
            unique_vals = list(attr_info['unique_values'])[:10]
            if len(unique_vals) > 1:
                val_samples = ", ".join(str(v)[:80] for v in unique_vals)
                if len(attr_info['unique_values']) > 10:
                    val_samples += f" ... (+{len(attr_info['unique_values']) - 10} more)"
                report.append(f"  - **Sample unique values**: {val_samples}")
        
        # Show sample value if available
        if sample is not None and sample != 'N/A':
            sample_str = str(sample)
            if len(sample_str) > 200:
                sample_str = sample_str[:200] + "..."
            report.append(f"  - **Sample value**: `{sample_str}`")
        
        report.append("")
    
    # Add metadata attributes section
    report.append("## ATTRIBUTE METADATA (name, type, etc.)")
    report.append("-" * 40)
    report.append("")
    
    for attr_name in sorted(analysis['all_attributes'].keys()):
        if attr_name.endswith(('_name', '_type', '_valueAsString')):
            values = analysis['all_attributes'][attr_name]
            non_null = len([v for v in values if v is not None])
            if non_null > 0:
                report.append(f"### {attr_name}")
                report.append(f"  - **Non-null**: {non_null}/{len(values)}")
                unique_vals = set(v for v in values if v is not None)
                if len(unique_vals) <= 20:
                    report.append(f"  - **Values**: {', '.join(str(v)[:60] for v in unique_vals)}")
                report.append("")
    
    return "\n".join(report)


async def main():
    print("=" * 60)
    print("SWTR Team Task Analysis")
    print("=" * 60)
    print("Connecting to SWTR API...")
    print("Fetching team tasks from spaces: DMS, OLP, WMB")
    print("")
    
    # Fetch all tasks
    tasks = await fetch_all_tasks()
    
    if not tasks:
        print("No tasks found. Exiting.")
        return
    
    print(f"Analyzing {len(tasks)} tasks...")
    print("")
    
    # Analyze tasks
    analysis = analyze_all_tasks(tasks)
    
    # Generate and print report
    report = generate_report(analysis)
    print(report)
    
    # Save to file
    with open('swtr_team_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("\n" + "=" * 60)
    print("Report saved to: swtr_team_analysis_report.txt")
    
    # Also save as JSON
    with open('swtr_team_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print("JSON data saved to: swtr_team_analysis.json")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
