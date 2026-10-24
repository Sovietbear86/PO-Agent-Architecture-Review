"""Real team configuration loader from project's team_members.yaml."""

import os
import yaml
from pathlib import Path
from typing import Optional


def get_real_team_members() -> list[dict]:
    """Load real team members from project's team_members.yaml.

    Returns:
        List of team member dictionaries
    """
    # Look for config in multiple possible locations relative to CWD
    possible_paths = [
        Path(os.getcwd()) / "task-api" / "config" / "team_members.yaml",
        Path(os.getcwd()).parent / "task-api" / "config" / "team_members.yaml",
    ]

    for config_path in possible_paths:
        if config_path.exists():
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
            return data.get("members", [])

    return []


def get_team_member_by_login(login: str) -> Optional[dict]:
    """Get specific team member by login.

    Args:
        login: Member login to find

    Returns:
        Team member dict if found, None otherwise
    """
    members = get_real_team_members()
    for member in members:
        if member.get("login") == login:
            return member
    return None


def get_all_member_logins() -> list[str]:
    """Get all team member logins.

    Returns:
        List of member logins
    """
    members = get_real_team_members()
    return [m.get("login") for m in members if m.get("login")]
