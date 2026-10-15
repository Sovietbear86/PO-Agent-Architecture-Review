"""Conservative, read-only multi-goal coverage preflight (A229M2.1).

Not a router: never executes tools, infers task facts or synthesizes answers.
Only separately anchored, recognized goals can become coverage requirements.
Unsupported/ambiguous structures are not declared proven.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

_TASK_KEY = re.compile(r"\b[A-Z][A-Z0-9]{1,12}-\d+\b")
_COLLECTION = re.compile(
    r"(?i)\bзадач(?:и|у|а|ам|ами)?\s+"
    r"(?P<person>[А-ЯЁ][а-яё-]+)\s+в\s+(?P<space>[A-Z][A-Z0-9_-]{1,12})\b"
)
_HIERARCHY = re.compile(r"(?i)\bиерархи[юияей]|\bродител(?:ь|я|ей|ьск)")
_RELATIONS = re.compile(r"(?i)\bсвязанн(?:ые|ых|ыми|ой|ая)\s+(?:(?:с\s+(?:ней|ним|ними)\s+))?задач")
_LOOKUP = re.compile(r"(?i)\b(?:покажи|найди|открой)\s+задач[уаи]\s*")
_COMPARE = re.compile(r"(?i)\bсравн(?:и|ить|ение|ите)\b")


@dataclass(frozen=True)
class RequestGoal:
    goal_id: str
    kind: str
    span: tuple[int, int]
    task_key: str = ""
    person: str = ""
    space: str = ""
    required_evidence: int = 1


@dataclass(frozen=True)
class GoalCoverage:
    goals: tuple[RequestGoal, ...]
    proven: tuple[str, ...]
    unproven: tuple[str, ...]
    evidence: dict[str, tuple[int, ...]]


def detect_goals(query: str) -> tuple[RequestGoal, ...]:
    """Recognize only independently anchored deliverables, never split on 'и'.

    This intentionally does NOT attempt general free-text semantic parsing:
    unknown goals need a future typed extractor, not false confidence.
    """
    text = str(query or "")
    found: list[tuple[int, int, str, str, str, str]] = []
    keys = list(_TASK_KEY.finditer(text))
    collections = list(_COLLECTION.finditer(text))
    for match in collections:
        found.append((
            match.start(), match.end(), "person_tasks", "",
            match.group("person"), match.group("space"),
        ))
    for match in keys:
        start, end = match.span()
        key = match.group()
        # A key is an independent lookup only when explicitly requested as a
        # task; hierarchy-only questions need only hierarchy evidence.
        preceding = text[max(0, start - 20):start]
        if _LOOKUP.search(preceding):
            found.append((start, end, "task_lookup", key, "", ""))
        suffix = text[end:]
        prefix = text[:start]
        if _HIERARCHY.search(suffix[:35]) or _HIERARCHY.search(prefix[max(0, len(prefix)-22):]):
            found.append((start, end, "task_hierarchy", key, "", ""))
        if _RELATIONS.search(suffix[:40]) or _RELATIONS.search(prefix[max(0, len(prefix)-30):]):
            found.append((start, end, "task_relations", key, "", ""))
    # Pronoun references ("её иерархию") must be bound to exactly one task
    # key; this is not an AS21 fact, only a user-requested deliverable.
    if len(keys) == 1 and _HIERARCHY.search(text) and not any(row[2] == "task_hierarchy" for row in found):
        k = keys[0]
        found.append((k.start(), k.end(), "task_hierarchy", k.group(), "", ""))
    if len(keys) == 1 and _RELATIONS.search(text) and not any(row[2] == "task_relations" for row in found):
        k = keys[0]
        found.append((k.start(), k.end(), "task_relations", k.group(), "", ""))
    # Comparisons are one deliverable even if two datasets are needed.
    # Defer reliable typing/verification of comparison goals to next stage.
    if _COMPARE.search(text):
        return ()
    distinct = sorted(set(found), key=lambda row: (row[0], row[2]))
    return tuple(
        RequestGoal(
            goal_id=f"g{i}", span=(start, end), kind=kind,
            task_key=key, person=person, space=space,
        )
        for i, (start, end, kind, key, person, space) in enumerate(distinct, 1)
    )


def _terminal_results(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("data")
    results = data.get("results") if isinstance(data, dict) else None
    return [r for r in results if isinstance(r, dict)] if isinstance(results, list) else []


def _person_stem_matches(source_name: str, requested: str) -> bool:
    """Match Russian genitive/nominative variants without broad fuzzy matching."""
    a = str(source_name or "").strip().casefold()
    b = str(requested or "").strip().casefold()
    if not a or not b:
        return False
    if a == b:
        return True
    # Bound to a short inflection suffix; arbitrary short common prefixes
    # may not certify two independently requested people's tasks.
    shorter, longer = sorted((a, b), key=len)
    return len(shorter) >= 6 and len(longer) - len(shorter) <= 2 and longer.startswith(shorter)


def _person_identity_matches(
    terminal_person: str,
    requested: str,
    result_rows: list[dict[str, Any]],
) -> bool:
    if _person_stem_matches(terminal_person, requested):
        return True

    # A canonical login may only be matched through a REAL member.resolve
    # observation from THIS trajectory. Never infer a surname from a login.
    for row in result_rows:
        if row.get("capability_id") != "member.resolve":
            continue
        args = row.get("arguments")
        data = row.get("data")
        if not isinstance(args, dict) or not isinstance(data, dict):
            continue
        if data.get("source_unavailable") or data.get("source_complete") is False:
            continue
        if not _person_stem_matches(
            str(args.get("reference") or args.get("person") or ""),
            requested,
        ):
            continue
        resolved = (
            data.get("member_login") or data.get("login")
            or data.get("assignee_id") or data.get("member_id")
        )
        if resolved is not None and str(resolved).casefold() == terminal_person.casefold():
            return True
    return False


def check_goal_coverage(response: dict[str, Any], goals: tuple[RequestGoal, ...]) -> GoalCoverage:
    """Bind each goal to terminal evidence with matching source arguments.

    Conservative: a resolver or text-only response never proves a goal.
    """
    result_rows = _terminal_results(response)
    evidence: dict[str, tuple[int, ...]] = {}
    proven: list[str] = []
    unproven: list[str] = []
    for goal in goals:
        matches: list[int] = []
        for i, row in enumerate(result_rows):
            cap = str(row.get("capability_id") or "")
            args = row.get("arguments")
            if not isinstance(args, dict):
                continue
            key = str(args.get("task_key") or args.get("key") or args.get("reference") or "").upper()
            if goal.kind == "task_lookup":
                valid = cap == "task.lookup" and key == goal.task_key
            elif goal.kind == "task_hierarchy":
                valid = cap == "task.hierarchy" and key == goal.task_key
            elif goal.kind == "task_relations":
                valid = cap in ("task.hierarchy", "task.relations") and key == goal.task_key
            elif goal.kind == "person_tasks":
                person_value = str(args.get("reference") or args.get("assignee") or "")
                space_value = str(args.get("space") or "")
                valid = (
                    cap.startswith("task.search")
                    and _person_identity_matches(person_value, goal.person, result_rows)
                    and space_value.upper() == goal.space.upper()
                )
            else:
                valid = False
            if valid:
                # Never count a failed/unavailable observation as proof.
                data = row.get("data")
                if not isinstance(data, dict) or data.get("source_unavailable") or data.get("source_complete") is False:
                    continue
                matches.append(i)
        evidence[goal.goal_id] = tuple(matches)
        (proven if matches else unproven).append(goal.goal_id)
    return GoalCoverage(goals, tuple(proven), tuple(unproven), evidence)



# Carry only compact source-verified observations; never expose these in HTTP.
_MAX_CARRIED_OBSERVATIONS = 6
_MAX_CARRIED_STATE_BYTES = 8192
_PROVENANCE = frozenset({"REAL_AS21"})
# Explicitly source-grounded canonical fields needed for planning/coverage.
# In particular, never retain task.source_data or SWTR attribute cards.
_CANONICAL_FIELDS = frozenset({
    "source", "source_complete", "capability", "task_key", "key", "id",
    "title", "status", "status_category", "status_type", "task_type",
    "task_type_code", "task_type_name", "space", "project_space",
    "assignee", "assignee_id", "assignee_login", "member_login",
    "member_id", "login", "count", "task_key_count", "task_keys_sample",
    "task_keys", "parent_chain", "depth", "root_key", "epic_key",
    "related_keys", "link_types", "created_at", "updated_at",
    "member", "task",
})
_NESTED_CANONICAL_FIELDS = _CANONICAL_FIELDS - frozenset({"member", "task"})


def _canonical_continuation_data(raw: dict[str, Any]) -> dict[str, Any]:
    """Strict allowlist after planner compaction, omitting ALL raw source cards."""
    def trim(value: Any, *, nested: bool = False) -> Any:
        if isinstance(value, list):
            return [trim(item, nested=True) for item in value]
        if not isinstance(value, dict):
            return value
        allowed = _NESTED_CANONICAL_FIELDS if nested else _CANONICAL_FIELDS
        return {
            key: trim(item, nested=True)
            for key, item in value.items() if key in allowed
        }
    return trim(raw)


def _build_internal_continuation(
    response: dict[str, Any], coverage: GoalCoverage,
) -> list[dict[str, Any]]:
    """Supply trusted, compact observations for the existing V4 resume seam.

    Missing or ambiguous provenance => nothing carried. Do not claim
    continuity from unverified data or pin imagined completion skills.
    """
    from po_agent.harness.agent_core_v4 import AgentCoreV4Runtime

    rows = _terminal_results(response)
    used_indexes = {
        i for goal_id in coverage.proven for i in coverage.evidence[goal_id]
    }
    # Resolver observations can be used as dependencies only when they come
    # from the same verified source-bound trajectory.
    candidate_indexes = [
        i for i, row in enumerate(rows)
        if i in used_indexes or str(row.get("capability_id") or "") in (
            "member.resolve", "space.resolve"
        )
    ]
    if len(candidate_indexes) > _MAX_CARRIED_OBSERVATIONS:
        return []

    saved: list[dict[str, Any]] = []
    for index in candidate_indexes:
        row = rows[index]
        cap = str(row.get("capability_id") or "")
        args = row.get("arguments")
        data = row.get("data")
        if not isinstance(args, dict) or not isinstance(data, dict):
            return []
        if data.get("source") not in _PROVENANCE:
            return []
        if data.get("source_unavailable") or data.get("source_complete") is False:
            return []
        if any(not isinstance(k, str) or not isinstance(v, (str, int, float, bool))
               for k, v in args.items()):
            return []
        compact = _canonical_continuation_data(
            AgentCoreV4Runtime._compact_data(cap, data)
        )
        saved.append({
            "step": index + 1,
            "capability_id": cap,
            "arguments": {k: str(v) for k, v in args.items()},
            "answer": str(row.get("answer") or "")[:384],
            "data": compact,
        })
    if len(json.dumps(saved, ensure_ascii=False, default=str).encode("utf-8")) > _MAX_CARRIED_STATE_BYTES:
        return []
    return saved


def _credit_prior_observations(
    response: dict[str, Any], prior_observations: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    """Private evidence view; never alter the public result rows.

    The caller must supply observations restored from the server-side
    PendingClarification record, never user request content. Validate their
    compact source lineage, shape and bounds again before crediting them.
    """
    if not prior_observations or len(prior_observations) > _MAX_CARRIED_OBSERVATIONS:
        return response
    prior: list[dict[str, Any]] = []
    for observation in prior_observations:
        if not isinstance(observation, dict):
            return response
        cap = observation.get("capability_id")
        args = observation.get("arguments")
        data = observation.get("data")
        if not isinstance(cap, str) or not isinstance(args, dict) or not isinstance(data, dict):
            return response
        if data.get("source") not in _PROVENANCE or data.get("source_unavailable") or data.get("source_complete") is False:
            return response
        if _canonical_continuation_data(data) != data:
            return response
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in args.items()):
            return response
        prior.append({
            "capability_id": cap, "arguments": dict(args),
            "data": dict(data), "answer": str(observation.get("answer") or "")[:384],
        })
    if len(json.dumps(prior, ensure_ascii=False, default=str).encode("utf-8")) > _MAX_CARRIED_STATE_BYTES:
        return response
    data = response.get("data")
    if not isinstance(data, dict):
        return response
    # Distinct private envelope: previous proven observations receive credit
    # without being injected into public data.results or UI evidence.
    return {
        **response,
        "data": {**data, "results": prior + _terminal_results(response)},
    }


def guard_completed_goal_coverage(
    response: dict[str, Any], original_query: str, *, preserve_state: bool = False,
    trusted_prior_observations: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """Fail closed for proven multi-goal shapes with missing terminal evidence.

    No execution, no model-side factual inference, no answer repairs by phrase.
    Strip unsupported prose entirely, including incorrect negative claims.
    The existing API layer adds clarification_id and retains original query.
    """
    if response.get("status") != "COMPLETED":
        return response
    goals = detect_goals(original_query)
    if len(goals) < 2:
        return response
    coverage_view = _credit_prior_observations(response, trusted_prior_observations) if preserve_state else response
    coverage = check_goal_coverage(coverage_view, goals)
    if not coverage.unproven:
        return response
    unresolved = [g for g in goals if g.goal_id in coverage.unproven]
    response["status"] = "NEEDS_CLARIFICATION"
    response["answer"] = None
    response["question"] = (
        "Запрос выполнен не полностью. Не удалось подтвердить: "
        + "; ".join(f"{g.kind}: {original_query[g.span[0]:g.span[1]]}" for g in unresolved)
        + ". Уточните, какую часть выполнить следующим запросом."
    )
    response["options"] = []
    response["evidence"] = []
    response["warnings"] = list(response.get("warnings") or []) + ["v4_goal_coverage_incomplete"]
    data = response.get("data")
    if isinstance(data, dict):
        state = data.setdefault("_agent_core_v4", {})
        if isinstance(state, dict) and preserve_state:
            carried = _build_internal_continuation(coverage_view, coverage)
            if carried:
                state["continuation_observations"] = carried
                # The existing loaded skills are reused. Do not manufacture
                # missing-goal skill IDs or assert multi-goal completion.
                state["goal_continuation_pending"] = True
            else:
                response["warnings"].append("v4_goal_continuation_state_unavailable")
        data.pop("results", None)
        if isinstance(state, dict):
            state["goal_coverage"] = {
                "requested": len(goals), "proven": list(coverage.proven),
                "unproven": list(coverage.unproven),
            }
    return response
