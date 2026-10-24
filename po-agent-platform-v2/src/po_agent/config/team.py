"""Team Configuration loader and validator for PO Agent Platform v2.

Provides functionality to:
- Load team configuration from YAML files
- Validate team configurations
- Access team settings and members
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TeamMember(BaseModel):
    """Represents a team member."""

    login: str = Field(..., description="Username/login")
    name: str = Field(..., description="Full name")
    role: str = Field(..., description="Role/title")
    capacity_hours: int = Field(40, ge=0, le=160, description="Weekly capacity in hours")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    team_affiliation: str = Field("default", description="Team sub-group")


class SprintConfig(BaseModel):
    """Represents a sprint configuration."""

    id: str = Field(..., description="Sprint ID (e.g., WMB-SPRNT-4)")
    name: str = Field(..., description="Sprint name")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    goal: Optional[str] = Field(None, description="Sprint goal")


class TeamConfig(BaseModel):
    """Represents the full team configuration."""

    model_config = ConfigDict(extra="ignore")

    team: Dict[str, Any] = Field(..., description="Team metadata")
    sprints: Dict[str, SprintConfig] = Field(..., description="Sprint configurations")
    members: List[TeamMember] = Field(..., description="Team members")
    capacity: Dict[str, int] = Field(default_factory=dict, description="Capacity settings")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")


class TeamConfigLoader:
    """Loader for team configuration files."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize loader.

        Args:
            config_dir: Directory containing config files (defaults to 'config')
        """
        self.config_dir = Path(config_dir or "config")

    def load(self, filename: str = "team.yaml") -> TeamConfig:
        """Load team configuration from YAML file.

        Args:
            filename: Name of config file (default: team.yaml)

        Returns:
            Validated TeamConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        config_path = self.config_dir / filename

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        return TeamConfig.model_validate(data)

    def load_example(self) -> TeamConfig:
        """Load example team configuration.

        Returns:
            Validated TeamConfig instance from example file
        """
        return self.load("team.example.yaml")

    def get_member_by_login(self, config: TeamConfig, login: str) -> Optional[TeamMember]:
        """Get team member by login.

        Args:
            config: Team configuration
            login: Member login to find

        Returns:
            TeamMember if found, None otherwise
        """
        for member in config.members:
            if member.login == login:
                return member
        return None

    def get_all_members(self, config: TeamConfig) -> List[TeamMember]:
        """Get all team members.

        Args:
            config: Team configuration

        Returns:
            List of all team members
        """
        return config.members.copy()

    def get_current_sprint(self, config: TeamConfig) -> Optional[SprintConfig]:
        """Get current sprint from configuration.

        Args:
            config: Team configuration

        Returns:
            Current sprint config if available
        """
        if "current" in config.sprints:
            return config.sprints["current"]
        # Return first sprint as default
        if config.sprints:
            return list(config.sprints.values())[0]
        return None


class TeamConfigValidator:
    """Validator for team configuration."""

    @staticmethod
    def validate(config: TeamConfig) -> tuple[bool, List[str]]:
        """Validate team configuration.

        Args:
            config: TeamConfig to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Validate team name exists
        if not config.team.get("name"):
            errors.append("Team name is required")

        # Validate members list
        if not config.members:
            errors.append("At least one team member is required")

        # Validate each member
        for member in config.members:
            if not member.login:
                errors.append(f"Member {member.name}: login is required")
            if not member.name:
                errors.append(f"Member {member.login}: name is required")
            if not member.role:
                errors.append(f"Member {member.login}: role is required")
            if member.capacity_hours < 0:
                errors.append(f"Member {member.login}: capacity cannot be negative")

        # Validate sprints
        if not config.sprints:
            errors.append("At least one sprint is required")

        for sprint_id, sprint in config.sprints.items():
            if not sprint.id:
                errors.append(f"Sprint {sprint_id}: ID is required")
            if not sprint.name:
                errors.append(f"Sprint {sprint_id}: name is required")
            if not sprint.start_date:
                errors.append(f"Sprint {sprint_id}: start_date is required")
            if not sprint.end_date:
                errors.append(f"Sprint {sprint_id}: end_date is required")

        # Validate capacity
        if "weekly_hours" in config.capacity:
            if config.capacity["weekly_hours"] < 0:
                errors.append("Weekly hours cannot be negative")

        return len(errors) == 0, errors

    @staticmethod
    def validate_member_skills(member: TeamMember) -> bool:
        """Validate member has at least one skill.

        Args:
            member: TeamMember to validate

        Returns:
            True if valid, False otherwise
        """
        return len(member.skills) > 0 or member.role.lower() == "manager"
