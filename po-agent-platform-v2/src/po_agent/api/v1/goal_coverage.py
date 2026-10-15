"""Conservative, read-only multi-goal coverage preflight (A229M2.1).

Not a router: never executes tools, infers task facts or synthesizes answers.
Only separately anchored, recognized goals can become coverage requirements.
Unsupported/ambiguous structures are not declared proven.
"""
from __future__ import annotations

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
                    and person_value.casefold().startswith(goal.person.casefold())
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


def guard_completed_goal_coverage(response: dict[str, Any], original_query: str) -> dict[str, Any]:
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
    coverage = check_goal_coverage(response, goals)
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
        data.pop("results", None)
        state = data.setdefault("_agent_core_v4", {})
        if isinstance(state, dict):
            state["goal_coverage"] = {
                "requested": len(goals), "proven": list(coverage.proven),
                "unproven": list(coverage.unproven),
            }
    return response
