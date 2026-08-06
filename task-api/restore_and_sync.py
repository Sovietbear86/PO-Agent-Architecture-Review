#!/usr/bin/env python3
"""Restore database from backup and sync team tasks."""

import json
import sys
import os
import yaml

sys.path.insert(0, 'src')

from app.repositories.task_repository import TaskRepository
from sync_sprint_tasks import sync_sprint_tasks


def load_team_members():
    """Load team members from config."""
    config_file = 'config/team_members.yaml'
    with open(config_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return {m['login'].lower(): m['full_name'] for m in data.get('members', [])}


def is_team_member_task(task, team_members):
    """Check if task belongs to a team member (assigned_to or responsible)."""
    source_data = getattr(task, 'source_data', {}) or {}
    swtr_attrs = source_data.get('swtr_attributes', [])
    
    for attr in swtr_attrs:
        if isinstance(attr, dict):
            code = attr.get('code')
            value = attr.get('value', {})
            if isinstance(value, dict):
                login = value.get('login', '').lower()
                if login in team_members:
                    return True
    return False


def sync_team_tasks():
    """Sync only team member tasks from all spaces."""
    spaces = ['WMB', 'CRPV', 'OLP', 'DMS']
    max_results = 5000
    
    # Load team members
    team_members = load_team_members()
    print(f"Team members: {len(team_members)}")
    
    # Clear existing tasks
    repo = TaskRepository()
    existing_tasks = repo.find_all()
    print(f"Clearing {len(existing_tasks)} existing tasks...")
    for task in existing_tasks:
        try:
            repo.delete(task.id)
        except Exception as e:
            print(f"Failed to delete task {task.id}: {e}")
    
    # Sync new tasks
    all_tasks = []
    for space in spaces:
        print(f"\nSyncing from space: {space}")
        tasks = sync_sprint_tasks(space=space, max_results=max_results)
        all_tasks.extend(tasks)
        print(f"  Found {len(tasks)} tasks")
    
    # Filter to team member tasks only
    team_tasks = [t for t in all_tasks if is_team_member_task(t, team_members)]
    print(f"\nTotal tasks: {len(all_tasks)}")
    print(f"Team tasks: {len(team_tasks)}")
    
    # Save only team tasks
    saved = 0
    for task in team_tasks:
        if task.source_id:
            try:
                repo.save(task)
                saved += 1
            except Exception as e:
                print(f"Failed to save task {task.source_id}: {e}")
    
    print(f"\nSaved {saved} team tasks")
    print(f"Total in database: {len(repo.find_all())}")
    
    # Print summary by member
    member_tasks = {}
    for task in team_tasks:
        source_data = getattr(task, 'source_data', {}) or {}
        swtr_attrs = source_data.get('swtr_attributes', [])
        for attr in swtr_attrs:
            if isinstance(attr, dict):
                code = attr.get('code')
                value = attr.get('value', {})
                if isinstance(value, dict):
                    login = value.get('login', '').lower()
                    if login in team_members:
                        if login not in member_tasks:
                            member_tasks[login] = []
                        member_tasks[login].append(task)
                        break
    
    print("\nTasks per team member:")
    for login in sorted(member_tasks.keys()):
        full_name = team_members.get(login, login)
        print(f"  {login} ({full_name}): {len(member_tasks[login])} задач")


if __name__ == '__main__':
    sync_team_tasks()
