"""Skill models for PO Agent Platform v2.

Skill - версионируемое декларативное описание способа решения класса задач.

SkillDefinition fields:
- skill_id: unique identifier (e.g., "task_search", "sprint_health")
- name: human-readable name
- version: semantic version (e.g., "1.0.0")
- status: candidate/active/deprecated/rejected
- intents: list of intent patterns that trigger this skill
- description: what the skill does
- required_context: list of required context fields
- optional_context: list of optional context fields
- clarification_policy: when to ask for clarification
- allowed_capabilities: list of capabilities skill can use
- workflow: list of workflow steps
- output_contract: expected output format
- prompt_references: related prompts
- fallback_policy: what to do on failure
- eval_tags: tags for evaluation

Status values:
- candidate: under evaluation
- active: currently in use
- deprecated: scheduled for removal
- rejected: not approved

Clarification policy:
- "always": always ask for missing required context
- "when_ambiguous": ask only when context is ambiguous
- "never": use defaults, never ask
- "auto": use session memory, ask only if not found

Workflow steps (example for sprint_health):
1. resolve_context
2. load_sprint
3. calculate_metrics
4. evaluate_risks
5. synthesize_response
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class SkillStatus(Enum):
    """Status of a skill."""
    CANDIDATE = "candidate"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class ClarificationPolicy(Enum):
    """When to ask for clarification."""
    ALWAYS = "always"
    WHEN_AMBIGUOUS = "when_ambiguous"
    NEVER = "never"
    AUTO = "auto"


class WorkflowStep(BaseModel):
    """Single step in skill workflow."""
    name: str
    description: Optional[str] = None
    capability: Optional[str] = None  # Which capability to call
    input_mapping: Optional[Dict[str, str]] = None  # Context field -> capability param
    output_mapping: Optional[Dict[str, str]] = None  # Capability result -> context field


class SkillDefinition(BaseModel):
    """Skill definition with versioning and metadata."""

    skill_id: str = Field(..., pattern=r"^[a-z_]+$")
    name: str
    version: str = Field(default="1.0.0")
    status: SkillStatus = SkillStatus.ACTIVE

    # Intents that trigger this skill
    intents: List[str] = Field(default_factory=list)

    # Description
    description: str = ""

    # Context requirements
    required_context: List[str] = Field(default_factory=list)
    optional_context: List[str] = Field(default_factory=list)

    # Clarification policy
    clarification_policy: ClarificationPolicy = ClarificationPolicy.AUTO

    # Allowed capabilities
    allowed_capabilities: List[str] = Field(default_factory=list)

    # Workflow steps
    workflow: List[WorkflowStep] = Field(default_factory=list)

    # Output contract
    output_contract: Dict[str, Any] = Field(default_factory=dict)

    # Prompt references
    prompt_references: List[str] = Field(default_factory=list)

    # Fallback policy
    fallback_policy: str = "return_error"

    # Eval tags
    eval_tags: List[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    approved_by: Optional[str] = None

    # Version history
    version_history: List[Dict[str, Any]] = Field(default_factory=list)

    def activate(self, approved_by: Optional[str] = None) -> None:
        """Activate this skill version."""
        self.status = SkillStatus.ACTIVE
        self.updated_at = datetime.now()
        self.approved_by = approved_by

    def deprecate(self) -> None:
        """Deprecate this skill version."""
        self.status = SkillStatus.DEPRECATED
        self.updated_at = datetime.now()

    def reject(self) -> None:
        """Reject this skill version."""
        self.status = SkillStatus.REJECTED
        self.updated_at = datetime.now()

    def add_version(
        self,
        new_version: str,
        changes: str,
        approved_by: Optional[str] = None,
    ) -> None:
        """Add a new version to history."""
        self.version_history.append({
            "version": new_version,
            "created_at": datetime.now().isoformat(),
            "changes": changes,
            "approved_by": approved_by,
        })
        self.version = new_version

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "intents": self.intents,
            "description": self.description,
            "required_context": self.required_context,
            "optional_context": self.optional_context,
            "clarification_policy": self.clarification_policy.value,
            "allowed_capabilities": self.allowed_capabilities,
            "workflow": [w.model_dump() for w in self.workflow],
            "output_contract": self.output_contract,
            "prompt_references": self.prompt_references,
            "fallback_policy": self.fallback_policy,
            "eval_tags": self.eval_tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Export for convenience
__all__ = [
    "SkillStatus",
    "ClarificationPolicy",
    "WorkflowStep",
    "SkillDefinition",
]
