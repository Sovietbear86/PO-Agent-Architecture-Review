"""Knowledge Layer V1 for PO Agent Platform v2.

Loads and manages knowledge sources:
- Product descriptions
- Team roles
- Workflow
- Metric definitions
- Release rules
- Approved curated memory

No vector DB unless justified.
"""

from pathlib import Path
import yaml
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class StatusInfo(BaseModel):
    """Status definition."""
    display_name: str
    category: str
    description: str


class WorkflowConfig(BaseModel):
    """Workflow configuration."""
    statuses: Dict[str, StatusInfo]
    analytics: Dict[str, List[str]]
    cycle_time: Dict[str, Any]
    wip: Dict[str, List[str]]
    throughput: Dict[str, List[str]]
    blockage: Dict[str, Any]


class TeamMember(BaseModel):
    """Team member definition."""
    login: str
    name: str
    role: str
    capacity_hours: int
    skills: List[str]
    team_affiliation: str


class TeamConfig(BaseModel):
    """Team configuration."""
    name: str
    description: str
    domain: str
    sprints: Dict[str, Any]
    members: List[TeamMember]
    capacity: Dict[str, int]
    settings: Dict[str, Any]


class ProductConfig(BaseModel):
    """Product configuration."""
    name: str
    description: str
    domain: str
    team: str


class MetricDefinition(BaseModel):
    """Metric definition."""
    name: str
    description: str
    formula: str
    unit: str
    category: str


class ReleaseRule(BaseModel):
    """Release rule."""
    name: str
    description: str
    condition: str
    severity: str


class CuratedMemoryEntry(BaseModel):
    """Curated memory entry."""
    key: str
    category: str
    content: str
    evidence_trace_ids: List[str]
    source: str
    confidence: float
    status: str  # candidate, approved, rejected, deprecated
    created_at: str
    approved_by: Optional[str] = None


class KnowledgeLoader:
    """Knowledge Layer loader for PO Agent Platform v2."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize knowledge loader.

        Args:
            config_dir: Path to config directory (default: ./config)
        """
        self.config_dir = Path(config_dir or "./config")
        self.workflow_config: Optional[WorkflowConfig] = None
        self.team_config: Optional[TeamConfig] = None
        self.product_configs: List[ProductConfig] = []
        self.metric_definitions: List[MetricDefinition] = []
        self.release_rules: List[ReleaseRule] = []
        self.curated_memory: List[CuratedMemoryEntry] = []

    def load_workflow(self, filepath: Optional[str] = None) -> WorkflowConfig:
        """Load workflow configuration.

        Args:
            filepath: Path to workflow YAML file

        Returns:
            WorkflowConfig object
        """
        path = Path(filepath or self.config_dir / "workflow.yaml")
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        self.workflow_config = WorkflowConfig(**data)
        return self.workflow_config

    def load_team(self, filepath: Optional[str] = None) -> TeamConfig:
        """Load team configuration.

        Args:
            filepath: Path to team YAML file

        Returns:
            TeamConfig object
        """
        path = Path(filepath or self.config_dir / "team.example.yaml")
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Handle nested structure (team: {...})
        team_data = data.get("team", data) if isinstance(data, dict) else data
        self.team_config = TeamConfig(**team_data)
        return self.team_config

    def load_products(self, filepath: Optional[str] = None) -> List[ProductConfig]:
        """Load product configurations.

        Args:
            filepath: Path to products YAML file

        Returns:
            List of ProductConfig objects
        """
        path = Path(filepath or self.config_dir / "products.yaml")

        if not path.exists():
            return []

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        self.product_configs = [ProductConfig(**p) for p in data.get("products", [])]
        return self.product_configs

    def load_metrics(self, filepath: Optional[str] = None) -> List[MetricDefinition]:
        """Load metric definitions.

        Args:
            filepath: Path to metrics YAML file

        Returns:
            List of MetricDefinition objects
        """
        path = Path(filepath or self.config_dir / "metrics.yaml")

        if not path.exists():
            return []

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        self.metric_definitions = [MetricDefinition(**m) for m in data.get("metrics", [])]
        return self.metric_definitions

    def load_release_rules(self, filepath: Optional[str] = None) -> List[ReleaseRule]:
        """Load release rules.

        Args:
            filepath: Path to release rules YAML file

        Returns:
            List of ReleaseRule objects
        """
        path = Path(filepath or self.config_dir / "release_rules.yaml")

        if not path.exists():
            return []

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        self.release_rules = [ReleaseRule(**r) for r in data.get("rules", [])]
        return self.release_rules

    def load_curated_memory(self, filepath: Optional[str] = None) -> List[CuratedMemoryEntry]:
        """Load curated memory entries.

        Args:
            filepath: Path to curated memory YAML file

        Returns:
            List of CuratedMemoryEntry objects
        """
        path = Path(filepath or self.config_dir / "curated_memory.yaml")

        if not path.exists():
            return []

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        self.curated_memory = [CuratedMemoryEntry(**e) for e in data.get("entries", [])]
        return self.curated_memory

    def load_all(self) -> Dict[str, Any]:
        """Load all knowledge sources.

        Returns:
            Dictionary with all loaded knowledge
        """
        knowledge = {
            "workflow": self.load_workflow(),
            "team": self.load_team(),
            "products": self.load_products(),
            "metrics": self.load_metrics(),
            "release_rules": self.load_release_rules(),
            "curated_memory": self.load_curated_memory(),
        }
        return knowledge

    def get_approved_curated_memory(self) -> List[CuratedMemoryEntry]:
        """Get only approved curated memory entries."""
        return [e for e in self.curated_memory if e.status == "approved"]

    def get_active_workflow_statuses(self) -> List[str]:
        """Get active workflow statuses."""
        if not self.workflow_config:
            return []

        return (
            self.workflow_config.analytics.get("active_work_statuses", [])
            + self.workflow_config.analytics.get("waiting_statuses", [])
        )


class KnowledgeLayer:
    """Knowledge Layer V1 manager."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize knowledge layer.

        Args:
            config_dir: Path to config directory
        """
        self.loader = KnowledgeLoader(config_dir)
        self.knowledge: Dict[str, Any] = {}

    def initialize(self) -> None:
        """Load all knowledge sources."""
        self.knowledge = self.loader.load_all()

    def get_workflow_config(self) -> Optional[WorkflowConfig]:
        """Get workflow configuration."""
        return self.knowledge.get("workflow")

    def get_team_config(self) -> Optional[TeamConfig]:
        """Get team configuration."""
        return self.knowledge.get("team")

    def get_active_statuses(self) -> List[str]:
        """Get active workflow statuses."""
        return self.loader.get_active_workflow_statuses()

    def get_team_members(self) -> List[TeamMember]:
        """Get team members."""
        if not self.knowledge.get("team"):
            return []

        return self.knowledge["team"].members

    def get_metric_definitions(self) -> List[MetricDefinition]:
        """Get metric definitions."""
        return self.knowledge.get("metrics", [])

    def get_release_rules(self) -> List[ReleaseRule]:
        """Get release rules."""
        return self.knowledge.get("release_rules", [])

    def get_approved_curated_memory(self) -> List[CuratedMemoryEntry]:
        """Get approved curated memory entries."""
        return self.loader.get_approved_curated_memory()

    def close(self) -> None:
        """Close resources."""
        pass
