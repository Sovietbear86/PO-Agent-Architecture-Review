"""Deterministic skill-completion contracts for Agent Core v4.

Assignment 187 reliability hardening: the planner is stochastic at the
terminal READY turn even after a trajectory has already collected sufficient
source-backed observations.  This module defines a *typed* completion contract
per skill so the runtime can deterministically recognize that a loaded skill's
goal is source-satisfied — and complete the trajectory without asking the
model to mint a terminal READY decision.

Design invariants:
- The contract is evaluated only against typed trajectory state (capability
  ids, observation arguments and observation data fields).  It never parses
  the user query and contains no person/space/sprint/task literals.
- Fail closed: an empty trajectory, an uncontracted skill or any unmet
  requirement returns False, which retains normal planner behavior (including
  the model-READY path and clarification/typed-error handling).
- A terminal observation is only accepted when its authoritative data fields
  exist and are non-empty; explicit source not-found states (null task, null
  sprint_id, ``found: false``) are never treated as satisfied.
- A downstream collection must be *bound* to upstream canonical identities and
  must *cover* every user constraint that was resolved by a resolver
  capability earlier in the trajectory; otherwise the trajectory is not
  complete and the planner continues.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

# Resolver capabilities produce typed user constraints.  The mapping is
# capability-structural: (capability_id) -> ((constraint_role, data_key), ...).
# Only these resolver observations count as "resolved user constraints" for
# the coverage check; derived values (e.g. a task's own assignee) do not.
_CONSTRAINT_RESOLVERS: Mapping[str, tuple[tuple[str, str], ...]] = {
    "member.resolve": (("assignee", "member_login"),),
    "space.resolve": (("space", "space"),),
    "sprint.resolve": (("sprint_id", "sprint_id"),),
    "sprint.search": (("sprint_id", "sprint_id"),),
    "sprint.current": (("sprint_id", "sprint_id"),),
    "release.resolve": (("release_id", "release_id"),),
}


def _data_path(data: Mapping[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return False
    return True


def resolved_constraint_arguments(
    observations: Iterable[Any],
    allowed_arguments: Iterable[str],
) -> dict[str, str]:
    """Return uniquely resolved constraints that a capability can accept.

    This is a generic typed bridge from resolver observations to downstream
    capability arguments. It never parses query text and never guesses among
    multiple values for the same role. A value is eligible only when:
    - the role is explicitly present in the target capability schema; and
    - exactly one canonical value for that role has been source-resolved.

    The runtime may use these values to fill omitted optional arguments before
    executing a terminal capability, eliminating stochastic planner dependence
    while preserving fail-closed ambiguity semantics.
    """
    allowed = {str(item) for item in allowed_arguments}
    grouped: dict[str, set[str]] = {}
    for role, value in resolved_constraint_values(observations):
        if role not in allowed:
            continue
        grouped.setdefault(role, set()).add(value)
    return {
        role: next(iter(values))
        for role, values in grouped.items()
        if len(values) == 1
    }


def resolved_constraint_values(observations: Iterable[Any]) -> list[tuple[str, str]]:
    """Typed user constraints resolved by resolver capabilities in the trajectory."""
    resolved: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for observation in observations:
        for role, data_key in _CONSTRAINT_RESOLVERS.get(observation.capability_id, ()):
            value = _data_path(observation.data, data_key) if isinstance(observation.data, Mapping) else None
            if not _nonempty(value):
                continue
            item = (role, str(value).strip())
            if item not in seen:
                seen.add(item)
                resolved.append(item)
    return resolved


@dataclass(frozen=True)
class CompletionRequirement:
    """One terminal observation requirement of a skill completion contract.

    capability_id:
        The capability whose successful observation satisfies this requirement.
    data_keys:
        Dotted data paths that must exist with a non-empty authoritative value
        (rejects explicit source not-found states such as ``task: null``).
    data_absent_keys:
        Top-level data keys that must NOT be present with a falsy value
        (rejects ``found: false`` not-found payloads).
    bound_argument:
        Optional ``(argument_name, upstream_capability, upstream_data_paths)``:
        the terminal observation's argument must equal a canonical identity
        value from a *preceding* observation of the upstream capability.
        This binds, e.g., a downstream task collection to the authoritative
        assignee of an upstream task lookup.
    covers_resolved_constraints:
        When true, the union of this requirement's terminal observations'
        arguments must include every user constraint resolved by a resolver
        capability earlier in the trajectory.  A collection that drops a
        resolved constraint never completes the skill.
    """

    capability_id: str
    data_keys: tuple[str, ...] = ()
    data_absent_keys: tuple[str, ...] = ()
    bound_argument: tuple[str, str, tuple[str, ...]] | None = None
    covers_resolved_constraints: bool = False


@dataclass(frozen=True)
class SkillCompletionContract:
    """All terminal observations a skill requires before it is source-satisfied."""

    skill_id: str
    requirements: tuple[CompletionRequirement, ...]


def _observation_matches_base(observation: Any, requirement: CompletionRequirement) -> bool:
    if observation.capability_id != requirement.capability_id:
        return False
    data = observation.data
    if not isinstance(data, Mapping):
        return False
    for path in requirement.data_keys:
        if not _nonempty(_data_path(data, path)):
            return False
    for key in requirement.data_absent_keys:
        if key in data and not data[key]:
            return False
    return True


def _bound_identity_matches(
    candidate: Any, requirement: CompletionRequirement, observations: list[Any]
) -> bool:
    argument_name, upstream_capability, upstream_paths = requirement.bound_argument  # type: ignore[misc]
    target = str(candidate.arguments.get(argument_name) or "").strip().casefold()
    if not target:
        return False
    for upstream in observations:
        if upstream.capability_id != upstream_capability:
            continue
        if not isinstance(upstream.data, Mapping) or upstream.step >= candidate.step:
            continue
        for path in upstream_paths:
            value = _data_path(upstream.data, path)
            if _nonempty(value) and str(value).strip().casefold() == target:
                return True
    return False


def _constraints_covered(
    candidates: list[Any], requirement: CompletionRequirement, observations: list[Any]
) -> bool:
    if not requirement.covers_resolved_constraints:
        return True
    covered: set[str] = set()
    for candidate in candidates:
        for value in candidate.arguments.values():
            text = str(value).strip().casefold()
            if text:
                covered.add(text)
    for _role, value in resolved_constraint_values(observations):
        if value.casefold() not in covered:
            return False
    return True


def _requirement_satisfied(requirement: CompletionRequirement, observations: list[Any]) -> bool:
    candidates = [observation for observation in observations if _observation_matches_base(observation, requirement)]
    if not candidates:
        return False
    if requirement.bound_argument is not None and not any(
        _bound_identity_matches(candidate, requirement, observations) for candidate in candidates
    ):
        return False
    if not _constraints_covered(candidates, requirement, observations):
        return False
    return True


def is_skill_satisfied(contract: SkillCompletionContract, observations: Iterable[Any]) -> bool:
    """True when the typed trajectory proves the skill's goal source-satisfied.

    Fails closed: an empty trajectory or any unmet requirement returns False,
    which retains normal planner behavior.
    """
    typed_observations = list(observations)
    if not typed_observations or not contract.requirements:
        return False
    return all(_requirement_satisfied(requirement, typed_observations) for requirement in contract.requirements)


def all_loaded_skills_satisfied(
    contracts: Mapping[str, SkillCompletionContract],
    loaded_skills: tuple[str, ...],
    observations: Iterable[Any],
) -> bool:
    """Runtime completion predicate over the full loaded-skill set.

    Auto-completion is allowed only when *every* loaded skill has a declared
    contract and *every* contract is satisfied by typed observations.  A skill
    without a contract (or with an unmet contract) keeps normal planner
    behavior, so the trajectory is never silently terminated while a user
    constraint or goal is still open.
    """
    typed_observations = list(observations)
    if not typed_observations or not loaded_skills:
        return False
    contracts_for_loaded = [contracts.get(skill_id) for skill_id in loaded_skills]
    if any(contract is None for contract in contracts_for_loaded):
        return False
    return all(
        is_skill_satisfied(contract, typed_observations)
        for contract in contracts_for_loaded
        if contract is not None
    )

def completion_frontier_skills(
    contracts: Mapping[str, SkillCompletionContract],
    loaded_skills: tuple[str, ...],
    observations: Iterable[Any],
) -> tuple[str, ...]:
    """Return the generic set of loaded skills that still govern completion.

    A planner may load a broad collection skill, resolve a few helper entities,
    and then pivot to a more-specific skill before ever executing the broad
    skill's terminal capability. Requiring the abandoned skill's contract
    forever makes deterministic completion impossible even when the later
    specialized capability succeeds.

    Frontier rules are structural, not semantic:
    - the latest loaded contracted skill is always required;
    - any earlier contracted skill whose required capability has actually been
      observed is "engaged" and remains required;
    - earlier loaded skills with no observation of any of their required
      capabilities are treated as superseded registration/planning attempts;
    - if the latest loaded skill has no contract, deterministic completion is
      unavailable (normal planner READY semantics remain).

    No query text, entity literal or skill-specific branch is consulted.
    """
    if not loaded_skills:
        return ()
    latest = loaded_skills[-1]
    if latest not in contracts:
        return ()

    typed_observations = list(observations)
    observed_capabilities = {obs.capability_id for obs in typed_observations}
    frontier: list[str] = []
    for skill_id in loaded_skills:
        contract = contracts.get(skill_id)
        if contract is None:
            continue
        engaged = any(
            requirement.capability_id in observed_capabilities
            for requirement in contract.requirements
        )
        if engaged or skill_id == latest:
            frontier.append(skill_id)
    return tuple(frontier)


def completion_frontier_satisfied(
    contracts: Mapping[str, SkillCompletionContract],
    loaded_skills: tuple[str, ...],
    observations: Iterable[Any],
) -> bool:
    """True when every structurally active skill on the completion frontier is satisfied."""
    typed_observations = list(observations)
    frontier = completion_frontier_skills(contracts, loaded_skills, typed_observations)
    if not frontier:
        return False
    return all(
        is_skill_satisfied(contracts[skill_id], typed_observations)
        for skill_id in frontier
    )
