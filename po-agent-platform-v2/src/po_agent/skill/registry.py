"""Skill Registry for PO Agent Platform v2.

Loads and validates skill definitions, stores versions, tracks active version.

Features:
- Load skill definitions from file or dict
- Validate skill definitions
- Track versions per skill_id
- Get active version
- Get all versions
- Promote candidate to active (requires human approval)

Usage:
    registry = SkillRegistry()
    registry.load_skills_from_file("skills.yaml")
    registry.load_skills_from_dict(initial_skills)
    skill = registry.get_active_skill("sprint_health")
"""

import os
import yaml
from typing import Optional, List, Dict, Any

from po_agent.skill.models import SkillDefinition, SkillStatus


class SkillRegistry:
    """Registry for skill definitions.

    Stores multiple versions per skill_id and tracks which version is active.
    """

    def __init__(self):
        """Initialize skill registry."""
        self._skills: Dict[str, Dict[str, SkillDefinition]] = {}
        self._loaded_at: Optional[str] = None

    def load_skills_from_dict(self, skills: List[Dict[str, Any]]) -> int:
        """Load skills from dictionary.

        Args:
            skills: List of skill definition dicts

        Returns:
            Number of skills loaded
        """
        loaded_count = 0

        for skill_dict in skills:
            try:
                skill = SkillDefinition.model_validate(skill_dict)
                self._add_skill(skill)
                loaded_count += 1
            except Exception as e:
                print(f"Failed to load skill: {skill_dict.get('skill_id', 'unknown')}: {e}")

        self._loaded_at = str(len(skills))
        return loaded_count

    def load_skills_from_file(self, file_path: str) -> int:
        """Load skills from YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            Number of skills loaded
        """
        if not os.path.exists(file_path):
            print(f"Skill file not found: {file_path}")
            return 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            skills = data.get('skills', [])
            return self.load_skills_from_dict(skills)
        except Exception as e:
            print(f"Failed to load skills from file: {e}")
            return 0

    def _add_skill(self, skill: SkillDefinition) -> None:
        """Add skill to registry.

        Args:
            skill: Skill definition
        """
        skill_id = skill.skill_id

        if skill_id not in self._skills:
            self._skills[skill_id] = {}

        # Store by version
        self._skills[skill_id][skill.version] = skill

    def get_active_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """Get active version of skill.

        Args:
            skill_id: Skill ID

        Returns:
            Active skill definition or None
        """
        if skill_id not in self._skills:
            return None

        # Get all versions for this skill
        versions = self._skills[skill_id]

        # Find active version
        for version, skill in versions.items():
            if skill.status == SkillStatus.ACTIVE:
                return skill

        # If no active, return first available
        if versions:
            return list(versions.values())[0]

        return None

    def get_skill_version(self, skill_id: str, version: str) -> Optional[SkillDefinition]:
        """Get specific version of skill.

        Args:
            skill_id: Skill ID
            version: Version string

        Returns:
            Skill definition or None
        """
        if skill_id not in self._skills:
            return None

        return self._skills[skill_id].get(version)

    def get_all_versions(self, skill_id: str) -> List[SkillDefinition]:
        """Get all versions of a skill.

        Args:
            skill_id: Skill ID

        Returns:
            List of skill definitions
        """
        if skill_id not in self._skills:
            return []

        return list(self._skills[skill_id].values())

    def get_all_skills(self) -> Dict[str, List[SkillDefinition]]:
        """Get all skills grouped by skill_id.

        Returns:
            Dict mapping skill_id to list of versions
        """
        return dict(self._skills)

    def get_active_skills(self) -> List[SkillDefinition]:
        """Get all active skills.

        Returns:
            List of active skill definitions
        """
        active = []
        for skill_id, versions in self._skills.items():
            for skill in versions.values():
                if skill.status == SkillStatus.ACTIVE:
                    active.append(skill)
                    break
        return active

    def register_new_version(
        self,
        skill_id: str,
        new_version: str,
        changes: str = "",
        approved_by: Optional[str] = None,
    ) -> Optional[SkillDefinition]:
        """Create a new version from existing skill.

        Args:
            skill_id: Skill ID
            new_version: New version string
            changes: Description of changes
            approved_by: User who approved

        Returns:
            New skill definition or None
        """
        base_skill = self.get_active_skill(skill_id)
        if base_skill is None:
            print(f"Active skill not found: {skill_id}")
            return None

        # Create new version based on base
        new_skill = SkillDefinition(
            skill_id=skill_id,
            name=base_skill.name,
            version=new_version,
            status=SkillStatus.CANDIDATE,
            intents=base_skill.intents.copy(),
            description=base_skill.description,
            required_context=base_skill.required_context.copy(),
            optional_context=base_skill.optional_context.copy(),
            clarification_policy=base_skill.clarification_policy,
            allowed_capabilities=base_skill.allowed_capabilities.copy(),
            workflow=[w.model_copy() for w in base_skill.workflow],
            output_contract=dict(base_skill.output_contract),
            prompt_references=base_skill.prompt_references.copy(),
            fallback_policy=base_skill.fallback_policy,
            eval_tags=base_skill.eval_tags.copy(),
            approved_by=approved_by,
        )

        self._add_skill(new_skill)
        return new_skill

    def promote_candidate(
        self,
        skill_id: str,
        version: str,
        approved_by: str,
    ) -> bool:
        """Promote candidate skill to active.

        Args:
            skill_id: Skill ID
            version: Version to promote
            approved_by: User who approved

        Returns:
            True if promoted, False otherwise
        """
        skill = self.get_skill_version(skill_id, version)
        if skill is None:
            return False

        if skill.status != SkillStatus.CANDIDATE:
            print(f"Skill is not a candidate: {skill_id} v{version}")
            return False

        # Deactivate current active version
        for v, s in self._skills[skill_id].items():
            if s.status == SkillStatus.ACTIVE:
                s.deprecate()

        # Activate new version
        skill.activate(approved_by)
        return True

    def count_skills(self) -> int:
        """Count total number of skill definitions.

        Returns:
            Number of skills
        """
        return sum(len(versions) for versions in self._skills.values())

    def count_active_skills(self) -> int:
        """Count active skills.

        Returns:
            Number of active skills
        """
        return len(self.get_active_skills())

    def has_skill(self, skill_id: str) -> bool:
        """Check if skill exists.

        Args:
            skill_id: Skill ID

        Returns:
            True if skill exists
        """
        return skill_id in self._skills


# Export for convenience
__all__ = ["SkillRegistry"]
