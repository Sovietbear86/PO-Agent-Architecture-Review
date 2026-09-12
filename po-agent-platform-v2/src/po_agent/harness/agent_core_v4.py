"""Agent Core v4 skill-native POC runtime.

This module is intentionally additive and deliberately does *not* depend on the
legacy semantic pre-pass.  The LLM sees the raw user request, progressively loads
procedural skills, calls a closed typed capability registry, observes source-backed
results and replans.  Existing proven executors are reused where appropriate.

V4 POC goal: demonstrate Hermes/PVM-Guru-like reasoning flexibility without
ad-hoc code generation, arbitrary endpoints, local task DB truth or entity/name
routing rules.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping

from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.task_api import AS21SourceError, AS21SourceUnavailable
from po_agent.llm.client import LLMClient, LLMMessage

from .contracts import CapabilityResult, Evidence, HarnessRequest, HarnessResponse, ResponseStatus
from .entity_grounding import TeamDirectory
from .production_entity_grounding_v2 import APPROVED_PRODUCT_SPACES


CapabilityHandlerV4 = Callable[[dict[str, str]], Awaitable[CapabilityResult]]


class V4ContractError(RuntimeError):
    pass


class V4NeedsClarification(RuntimeError):
    def __init__(self, question: str, *, options: tuple[str, ...] = ()) -> None:
        super().__init__(question)
        self.question = question
        self.options = options


@dataclass(frozen=True)
class CapabilitySpecV4:
    id: str
    summary: str
    arguments: Mapping[str, str]

    def compact(self) -> dict[str, Any]:
        return {"id": self.id, "summary": self.summary, "arguments": dict(self.arguments)}


@dataclass(frozen=True)
class SkillSpecV4:
    id: str
    summary: str
    procedure: tuple[str, ...]
    capabilities: tuple[str, ...]

    def compact(self) -> dict[str, str]:
        return {"id": self.id, "summary": self.summary}

    def detail(self, capability_specs: Mapping[str, CapabilitySpecV4]) -> dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "procedure": list(self.procedure),
            "capabilities": [capability_specs[item].compact() for item in self.capabilities],
        }


class SkillCatalogV4:
    """Compact-first procedural catalog.

    Entity facts are never stored here.  The catalog only describes reusable
    procedures and the capabilities they are allowed to use.
    """

    def __init__(self, skills: tuple[SkillSpecV4, ...], capabilities: Mapping[str, CapabilitySpecV4]) -> None:
        self._skills = {skill.id: skill for skill in skills}
        self._capabilities = dict(capabilities)
        if len(self._skills) != len(skills):
            raise ValueError("duplicate v4 skill id")
        for skill in skills:
            missing = [item for item in skill.capabilities if item not in self._capabilities]
            if missing:
                raise ValueError(f"skill {skill.id} references unknown capabilities: {missing}")

    def compact(self) -> tuple[dict[str, str], ...]:
        return tuple(self._skills[key].compact() for key in sorted(self._skills))

    def load(self, skill_id: str) -> dict[str, Any]:
        if skill_id not in self._skills:
            raise V4ContractError(f"unknown skill: {skill_id}")
        return self._skills[skill_id].detail(self._capabilities)

    def allowed_capabilities(self, loaded_skills: tuple[str, ...]) -> frozenset[str]:
        result: set[str] = set()
        for skill_id in loaded_skills:
            skill = self._skills.get(skill_id)
            if skill:
                result.update(skill.capabilities)
        return frozenset(result)


@dataclass(frozen=True)
class V4Observation:
    step: int
    capability_id: str
    arguments: Mapping[str, str]
    answer: str
    data: Mapping[str, Any]

    def planner_view(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "capability_id": self.capability_id,
            "arguments": dict(self.arguments),
            "answer": self.answer,
            "data": dict(self.data),
        }


@dataclass(frozen=True)
class V4Decision:
    kind: str
    skill_id: str | None = None
    capability_id: str | None = None
    arguments: Mapping[str, str] | None = None
    answer: str | None = None
    rationale: str | None = None


def _extract_json_object(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.I | re.S).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except Exception:
        pass
    start = text.find("{")
    while start >= 0:
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        value = json.loads(text[start:index + 1])
                    except Exception:
                        break
                    return value if isinstance(value, dict) else None
        start = text.find("{", start + 1)
    return None


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(token.casefold() for token in re.findall(r"[A-Za-zА-Яа-яЁё0-9_.-]+", text) if token)


def _literal_is_query_derived(value: str, query: str) -> bool:
    """Conservative anti-invention guard for planner literals.

    Exact substring is preferred.  A single inflected/name token is also allowed
    when it has a long common prefix with a query token; the authoritative source
    resolver still has to prove the final entity before it can be used.
    """
    raw = str(value or "").strip()
    if not raw:
        return False
    if raw.casefold() in query.casefold():
        return True
    wanted = _tokens(raw)
    available = _tokens(query)
    if len(wanted) != 1:
        return False
    token = wanted[0]
    if len(token) < 4:
        return False
    return any(len(os.path.commonprefix((token, candidate))) >= min(5, len(token), len(candidate)) for candidate in available)


# `os.path.commonprefix` above is string-based and deliberately used only as an
# anti-invention check; source-backed entity resolution remains authoritative.
import os


class SkillNativePlannerV4:
    """Raw-query planner with progressive skill disclosure.

    No semantic frame, intent label, person slot or clarification object is a
    prerequisite for execution.  The model may inspect skill procedures and then
    call only capabilities exposed by those loaded skills.
    """

    SYSTEM = """You are Agent Core v4, a skill-native Product Owner agent planner.
You solve requests by progressively loading procedural skills and calling governed tools.
You DO NOT receive or require a semantic-prepass JSON contract.

Return exactly ONE JSON object with keys: load_skill, call, ready, rationale.
Exactly one of load_skill/call/ready must be a non-null object.

LOAD SKILL:
{"load_skill":{"skill_id":"<id from compact_skill_catalog>"},"call":null,"ready":null,"rationale":"..."}

CALL:
{"load_skill":null,"call":{"capability_id":"<id exposed by a loaded skill>","arguments":{"name":"value"}},"ready":null,"rationale":"..."}

READY:
{"load_skill":null,"call":null,"ready":{"answer":"short synthesis instruction or answer"},"rationale":"..."}

Rules:
- First inspect the compact skill catalog and load the smallest relevant skill.
- Detailed tool contracts appear only after a skill is loaded.
- For a human name/surname that must become a source identity, call member.resolve; do not invent a login.
- For a sprint that must be validated, call sprint.resolve; for a product space call space.resolve when useful.
- Use observation references exactly as $obs.<step>.<field> for facts returned by prior calls.
- For person+sprint task requests, normally resolve the person and sprint, then call task.search with both constraints.
- For task-key analysis, use the task-key capability exposed by the loaded skill.
- Keep every user constraint through the trajectory.
- You may infer safe semantic enums such as status=not_completed from words meaning open/unresolved/not completed.
- Never invent people, logins, spaces, sprint ids, release ids, task ids, counts or source facts.
- If a required entity cannot be resolved by the available capabilities, use READY only to explain the limitation/clarification.
- After observations already support the complete answer, use READY instead of calling unrelated tools.
"""

    REPAIR = """The previous planner decision was invalid. Return one valid JSON decision only.
Choose exactly one branch: load_skill, call, or ready. Do not add keys. Do not invent source facts."""

    def __init__(self, client: LLMClient, *, model: str | None = None, max_steps: int = 8) -> None:
        self.client = client
        self.model = model
        self.max_steps = max(3, int(max_steps))

    @staticmethod
    def _decode(data: Mapping[str, Any]) -> V4Decision | None:
        branches = [name for name in ("load_skill", "call", "ready") if isinstance(data.get(name), Mapping)]
        if len(branches) != 1:
            return None
        rationale = str(data.get("rationale") or "").strip() or None
        branch = branches[0]
        payload = data[branch]
        if branch == "load_skill":
            skill_id = str(payload.get("skill_id") or "").strip()
            return V4Decision("load_skill", skill_id=skill_id, rationale=rationale) if skill_id else None
        if branch == "call":
            capability_id = str(payload.get("capability_id") or "").strip()
            args = payload.get("arguments")
            if not capability_id or not isinstance(args, Mapping):
                return None
            arguments = {str(k): str(v).strip() for k, v in args.items() if v not in (None, "") and str(v).strip()}
            return V4Decision("call", capability_id=capability_id, arguments=arguments, rationale=rationale)
        answer = str(payload.get("answer") or "").strip()
        return V4Decision("ready", answer=answer, rationale=rationale) if answer else None

    async def next_decision(
        self,
        *,
        user_query: str,
        catalog: SkillCatalogV4,
        loaded_skills: tuple[str, ...],
        observations: list[V4Observation],
    ) -> V4Decision:
        payload = {
            "user_query": user_query,
            "compact_skill_catalog": list(catalog.compact()),
            "loaded_skills": [catalog.load(skill_id) for skill_id in loaded_skills],
            "observations": [item.planner_view() for item in observations],
            "step_budget_remaining": self.max_steps - len(observations),
        }
        messages = [
            LLMMessage(role="system", content=self.SYSTEM),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]
        failures: list[str] = []
        for attempt in range(3):
            try:
                response = await self.client.complete(
                    messages,
                    model=self.model,
                    temperature=0.0,
                    max_tokens=800,
                )
            except Exception as exc:
                failures.append(type(exc).__name__)
                continue
            if not response.choices:
                failures.append("no_choices")
                continue
            raw = response.choices[0].message.content
            obj = _extract_json_object(raw)
            decision = self._decode(obj) if obj is not None else None
            if decision is not None:
                if decision.kind == "load_skill":
                    catalog.load(decision.skill_id or "")
                elif decision.kind == "call":
                    allowed = catalog.allowed_capabilities(loaded_skills)
                    if decision.capability_id not in allowed:
                        failures.append(f"capability_not_loaded:{decision.capability_id}")
                        messages.extend([
                            LLMMessage(role="assistant", content=raw or "{}"),
                            LLMMessage(role="user", content=self.REPAIR + " Load the relevant skill before calling its capability."),
                        ])
                        continue
                return decision
            failures.append("invalid_json_decision")
            messages.extend([
                LLMMessage(role="assistant", content=raw or "{}"),
                LLMMessage(role="user", content=self.REPAIR),
            ])
        raise V4ContractError(f"planner failed bounded repair: {failures}")


class ResponseSynthesizerV4:
    """Separate final prose from tool selection.

    The synthesizer only receives validated observations.  If it fails, callers
    fall back to deterministic concatenation of capability answers.
    """

    SYSTEM = """You write the final concise Russian answer for a Product Owner agent.
Use ONLY the supplied validated observations. Never invent ids, counts, people, statuses or source facts.
If observations contain a task collection, preserve its reported count. If a request has multiple parts, cover each part.
Do not mention internal planner machinery unless the user asks."""

    def __init__(self, client: LLMClient, *, model: str | None = None) -> None:
        self.client = client
        self.model = model

    async def synthesize(self, user_query: str, observations: list[V4Observation]) -> str:
        payload = {
            "user_query": user_query,
            "validated_observations": [item.planner_view() for item in observations],
        }
        response = await self.client.complete(
            [
                LLMMessage(role="system", content=self.SYSTEM),
                LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
            ],
            model=self.model,
            temperature=0.0,
            max_tokens=900,
        )
        if not response.choices or not str(response.choices[0].message.content or "").strip():
            raise V4ContractError("empty v4 synthesis")
        return str(response.choices[0].message.content).strip()


class AgentCoreV4Runtime:
    """Additive POC runtime for the first skill-native vertical slice."""

    _PLANNER_FREE_TEXT_LIMIT = 384
    _PLANNER_UNSTRUCTURED_FIELDS = frozenset({
        "description",
        "comment",
        "comments",
        "body",
        "details",
        "stacktrace",
        "stack_trace",
        "log",
        "logs",
        "raw",
        "raw_text",
    })

    def __init__(
        self,
        adapter: AS21Adapter,
        *,
        llm: LLMClient,
        model: str | None,
        team: TeamDirectory,
        legacy_capabilities: Any,
        max_steps: int = 8,
    ) -> None:
        self.adapter = adapter
        self.llm = llm
        self.model = model
        self.team = team
        self.legacy_capabilities = legacy_capabilities
        self.planner = SkillNativePlannerV4(llm, model=model, max_steps=max_steps)
        self.synthesizer = ResponseSynthesizerV4(llm, model=model)
        self._capability_specs = self._build_capability_specs()
        self.catalog = self._build_skill_catalog()
        self._handlers: dict[str, CapabilityHandlerV4] = {
            "member.resolve": self._member_resolve,
            "space.resolve": self._space_resolve,
            "sprint.resolve": self._sprint_resolve,
            "release.resolve": self._release_resolve,
            "task.search": self._task_search,
            "task.lookup": self._legacy("task.lookup"),
            "task.summary": self._legacy("task.summary"),
            "task.quality": self._legacy("task.quality"),
            "task.acceptance": self._legacy("task.acceptance_analysis"),
            "task.blockers": self._legacy("task.blockers"),
            "sprint.health": self._legacy("sprint.health"),
            "sprint.current": self._legacy("sprint.current"),
            "release.health": self._legacy("release.health"),
        }

    @staticmethod
    def _build_capability_specs() -> dict[str, CapabilitySpecV4]:
        return {
            "member.resolve": CapabilitySpecV4("member.resolve", "Resolve a human reference against REAL AS21 search_users.", {"reference": "required raw human reference"}),
            "space.resolve": CapabilitySpecV4("space.resolve", "Validate an approved product space.", {"reference": "required space text"}),
            "sprint.resolve": CapabilitySpecV4("sprint.resolve", "Validate a sprint id against REAL AS21 and return canonical id/space.", {"reference": "required sprint id", "space": "optional canonical space"}),
            "release.resolve": CapabilitySpecV4("release.resolve", "Validate a release/version id against REAL AS21 tasks.", {"reference": "required release id", "space": "optional canonical space"}),
            "task.search": CapabilitySpecV4("task.search", "Search REAL AS21 tasks by any resolved assignee/space/sprint/status combination.", {"assignee": "optional canonical login from member.resolve", "space": "optional approved space", "sprint_id": "optional canonical sprint", "status": "optional status; not_completed is supported"}),
            "task.lookup": CapabilitySpecV4("task.lookup", "Read one REAL AS21 task by key.", {"task_key": "required task key"}),
            "task.summary": CapabilitySpecV4("task.summary", "Summarize one REAL AS21 task.", {"task_key": "required task key"}),
            "task.quality": CapabilitySpecV4("task.quality", "Analyze one task's formulation quality.", {"task_key": "required task key"}),
            "task.acceptance": CapabilitySpecV4("task.acceptance", "Analyze acceptance criteria/testability for one task.", {"task_key": "required task key"}),
            "task.blockers": CapabilitySpecV4("task.blockers", "Analyze blockers/dependencies for one task.", {"task_key": "required task key"}),
            "sprint.health": CapabilitySpecV4("sprint.health", "Calculate current sprint health from REAL AS21 sprint tasks.", {"sprint_id": "required canonical sprint id"}),
            "sprint.current": CapabilitySpecV4("sprint.current", "Read the current sprint for a product space.", {"product": "required approved space"}),
            "release.health": CapabilitySpecV4("release.health", "Calculate release progress from REAL AS21 release tasks.", {"release_id": "required release id"}),
        }

    def _build_skill_catalog(self) -> SkillCatalogV4:
        skills = (
            SkillSpecV4(
                "tasks.search",
                "Find/filter tasks by person, product space, sprint and status.",
                (
                    "Resolve only the entities needed by the user's filters.",
                    "For a human reference call member.resolve; for a sprint call sprint.resolve.",
                    "Call task.search with every resolved user constraint and validate the returned collection.",
                ),
                ("member.resolve", "space.resolve", "sprint.resolve", "task.search"),
            ),
            SkillSpecV4(
                "tasks.lookup_then_assignee",
                "Read a task and then inspect tasks of its assignee.",
                (
                    "Call task.lookup for the user-supplied task key.",
                    "Use the authoritative assignee from the observation, never infer a person from prose.",
                    "Call task.search for that assignee and preserve any additional user filters.",
                ),
                ("task.lookup", "task.search"),
            ),
            SkillSpecV4("task.lookup", "Read one task by key.", ("Call task.lookup with the literal task key.",), ("task.lookup",)),
            SkillSpecV4("task.summary", "Explain/summarize one task.", ("Call task.summary with the literal task key.",), ("task.summary",)),
            SkillSpecV4("task.quality", "Assess task statement quality/completeness.", ("Call task.quality with the literal task key.",), ("task.quality",)),
            SkillSpecV4("task.acceptance", "Assess acceptance criteria/testability of a task.", ("Call task.acceptance with the literal task key.",), ("task.acceptance",)),
            SkillSpecV4("task.blockers", "Inspect blockers/dependencies of a task.", ("Call task.blockers with the literal task key.",), ("task.blockers",)),
            SkillSpecV4("sprint.health", "Show health/progress of a sprint.", ("Resolve/validate the sprint if needed, then call sprint.health.",), ("sprint.resolve", "sprint.health")),
            SkillSpecV4("sprint.current", "Find the current sprint for a product space.", ("Validate the product space, then call sprint.current.",), ("space.resolve", "sprint.current")),
            SkillSpecV4("release.health", "Show release health/progress.", ("Validate the release if useful, then call release.health.",), ("release.resolve", "release.health")),
        )
        return SkillCatalogV4(skills, self._capability_specs)

    def _legacy(self, capability_id: str) -> CapabilityHandlerV4:
        async def execute(args: dict[str, str]) -> CapabilityResult:
            return await self.legacy_capabilities.execute(capability_id, args)
        return execute

    @staticmethod
    def _safe_status(raw: str) -> str:
        value = str(raw or "").strip().casefold()
        if value in {"not_completed", "open", "open_tasks", "unresolved", "active", "открытые", "незакрытые"}:
            return "not_completed"
        if value in {"completed", "closed", "resolved", "done", "закрытые", "завершенные", "завершённые"}:
            return "completed"
        return str(raw or "").strip()

    @staticmethod
    def _task_to_dict(task: Any) -> dict[str, Any]:
        return {
            "key": task.key,
            "title": task.title,
            "status": task.status.value,
            "status_category": task.status_category.value,
            "assignee": task.assignee,
            "assignee_login": getattr(task, "assignee_login", None),
            "assignee_id": getattr(task, "assignee_id", None),
            "project_space": getattr(task, "project_space", None),
            "sprint_id": task.sprint_id,
            "release_id": task.release_id,
            "source": task.source,
        }

    async def _member_resolve(self, args: dict[str, str]) -> CapabilityResult:
        reference = str(args.get("reference") or "").strip()
        if not reference:
            raise V4NeedsClarification("Кого именно нужно найти?")

        # Production task-api adapters expose a governed resilient HTTP read path.
        # Use it for the REAL MCP-SWTR search_users facade.
        resilient_get = getattr(self.adapter, "_get_resilient", None)
        if resilient_get is not None:
            try:
                response = await resilient_get("/api/v1/swtr-read/assignees/resolve", params={"reference": reference})
                payload = response.json()
            except V4NeedsClarification:
                raise
            except AS21SourceUnavailable:
                raise
            except Exception as exc:
                http_response = getattr(exc, "response", None)
                status = getattr(http_response, "status_code", None)
                if status == 409:
                    detail_payload: dict = {}
                    try:
                        parsed = json.loads(http_response.content.decode())
                        detail = parsed.get("detail") if isinstance(parsed, dict) else None
                        if isinstance(detail, dict):
                            detail_payload = detail
                    except Exception:
                        detail_payload = {}
                    matches = detail_payload.get("matches") if isinstance(detail_payload, dict) else []
                    raise V4NeedsClarification(
                        f"Не удалось однозначно определить пользователя «{reference}».",
                        options=tuple(str(item) for item in matches if item),
                    ) from exc
                if status in {502, 503, 504}:
                    raise AS21SourceUnavailable("REAL AS21 identity resolver unavailable") from exc
                raise AS21SourceError("REAL AS21 identity resolver failed") from exc
            external_id = str(payload.get("external_id") or "").strip() if isinstance(payload, dict) else ""
            if not external_id:
                raise V4NeedsClarification(f"Не удалось подтвердить пользователя «{reference}» в AS21.")
            return CapabilityResult(
                answer=f"Пользователь подтверждён: {external_id}.",
                data={"reference": reference, "member_login": external_id, "external_id": external_id, "source": "REAL_AS21"},
                evidence=[Evidence(type="member_identity", source="as21", entity_id=external_id, label=reference, value=external_id)],
            )

        # Non-production/fake fallback is deterministic TeamDirectory only.
        matches = self.team.resolve_person(reference)
        if len(matches) != 1:
            raise V4NeedsClarification(
                f"Не удалось однозначно определить пользователя «{reference}».",
                options=tuple(item.login for item in matches),
            )
        login = matches[0].login
        return CapabilityResult(
            answer=f"Пользователь подтверждён: {login}.",
            data={"reference": reference, "member_login": login, "external_id": login, "source": "TEAM_DIRECTORY"},
            evidence=[Evidence(type="member_identity", source="team_directory", entity_id=login, label=reference, value=login)],
        )

    async def _space_resolve(self, args: dict[str, str]) -> CapabilityResult:
        reference = str(args.get("reference") or "").strip().upper()
        if reference not in APPROVED_PRODUCT_SPACES:
            raise V4NeedsClarification(
                f"Не удалось подтвердить пространство «{reference or '?'}» в разрешённом контуре.",
                options=tuple(sorted(APPROVED_PRODUCT_SPACES)),
            )
        return CapabilityResult(
            answer=f"Пространство подтверждено: {reference}.",
            data={"space": reference, "product": reference, "source": "PO_AGENT_SCOPE"},
        )

    async def _sprint_resolve(self, args: dict[str, str]) -> CapabilityResult:
        reference = str(args.get("reference") or "").strip().upper()
        if not reference:
            raise V4NeedsClarification("Какой спринт использовать?")
        inferred_space = reference.split("-SPRNT-", 1)[0] if "-SPRNT-" in reference else ""
        requested_space = str(args.get("space") or inferred_space).strip().upper() or None
        if requested_space and requested_space not in APPROVED_PRODUCT_SPACES:
            raise V4NeedsClarification(f"Пространство спринта «{requested_space}» не подтверждено.")
        tasks = await self.adapter.get_sprint_tasks(reference, requested_space)
        if not tasks:
            raise V4NeedsClarification(f"Не удалось подтвердить спринт «{reference}» по данным REAL AS21.")
        spaces = sorted({str(getattr(task, "project_space", "") or "").upper() for task in tasks if getattr(task, "project_space", None)})
        canonical_space = requested_space or (spaces[0] if len(spaces) == 1 else None)
        return CapabilityResult(
            answer=f"Спринт подтверждён: {reference}.",
            data={"sprint_id": reference, "space": canonical_space, "count": len(tasks), "source": "REAL_AS21"},
            evidence=[Evidence(type="sprint", source="as21", entity_id=reference, label="validated sprint", value=len(tasks))],
        )

    async def _release_resolve(self, args: dict[str, str]) -> CapabilityResult:
        reference = str(args.get("reference") or "").strip().upper()
        space = str(args.get("space") or "").strip().upper() or None
        if not reference:
            raise V4NeedsClarification("Какой релиз использовать?")
        tasks = await self.adapter.get_release_tasks(reference, space)
        if not tasks:
            raise V4NeedsClarification(f"Не удалось подтвердить релиз «{reference}» по данным REAL AS21.")
        return CapabilityResult(
            answer=f"Релиз подтверждён: {reference}.",
            data={"release_id": reference, "space": space, "count": len(tasks), "source": "REAL_AS21"},
            evidence=[Evidence(type="release", source="as21", entity_id=reference, label="validated release", value=len(tasks))],
        )

    async def _task_search(self, args: dict[str, str]) -> CapabilityResult:
        assignee = str(args.get("assignee") or "").strip()
        space = str(args.get("space") or "").strip().upper()
        sprint_id = str(args.get("sprint_id") or "").strip().upper()
        status = self._safe_status(args.get("status") or "")
        if space and space not in APPROVED_PRODUCT_SPACES:
            raise V4NeedsClarification(f"Пространство «{space}» не подтверждено.")
        if not any((assignee, sprint_id)):
            raise V4NeedsClarification("Для skill-native POC task.search нужен исполнитель и/или спринт; уточните фильтр.")

        tasks: list[Any]
        if assignee:
            query = f'assignee = "{assignee}"'
            if space:
                query += f' AND project = "{space}"'
            tasks = list(await self.adapter.search_tasks(query, max_results=10000))
        else:
            tasks = list(await self.adapter.get_sprint_tasks(sprint_id, space or None))

        if sprint_id:
            sprint_tasks = list(await self.adapter.get_sprint_tasks(sprint_id, space or None))
            sprint_keys = {task.key for task in sprint_tasks}
            tasks = [task for task in tasks if task.key in sprint_keys]

        if space:
            tasks = [task for task in tasks if str(getattr(task, "project_space", "") or "").casefold() == space.casefold()]

        if assignee:
            def identity_values(task: Any) -> set[str]:
                return {
                    str(value).strip().casefold()
                    for value in (
                        getattr(task, "assignee", None),
                        getattr(task, "assignee_login", None),
                        getattr(task, "assignee_id", None),
                    )
                    if value and str(value).strip()
                }
            tasks = [task for task in tasks if assignee.casefold() in identity_values(task)]

        if status == "not_completed":
            tasks = [task for task in tasks if not task.is_completed]
        elif status == "completed":
            tasks = [task for task in tasks if task.is_completed]
        elif status:
            tasks = [task for task in tasks if status.casefold() in task.status.value.casefold() or status.casefold() in task.status_category.value.casefold()]

        filters = {key: value for key, value in {"assignee": assignee, "space": space, "sprint_id": sprint_id, "status": status}.items() if value}
        rows = [self._task_to_dict(task) for task in tasks]
        answer = f"Найдено задач: {len(rows)}."
        return CapabilityResult(
            answer=answer,
            data={"count": len(rows), "filters": filters, "tasks": rows, "task_keys": [row["key"] for row in rows], "source": "REAL_AS21"},
            evidence=[Evidence(type="task", source="as21", entity_id=row["key"], label=row["title"], value=row["status"]) for row in rows],
        )

    @staticmethod
    def _resolve_observation_reference(value: str, observations: list[V4Observation]) -> str:
        raw = str(value or "").strip()
        if not raw.startswith("$obs."):
            return raw
        parts = raw.split(".")
        if len(parts) < 3:
            raise V4ContractError(f"malformed observation reference: {raw}")
        try:
            step = int(parts[1])
        except ValueError as exc:
            raise V4ContractError(f"invalid observation step: {raw}") from exc
        observation = next((item for item in observations if item.step == step), None)
        if observation is None:
            raise V4ContractError(f"observation not found: {raw}")
        current: Any = observation.data
        for key in parts[2:]:
            if not isinstance(current, Mapping) or key not in current:
                raise V4ContractError(f"observation path not found: {raw}")
            current = current[key]
        if isinstance(current, (str, int, float)) and str(current).strip():
            return str(current).strip()
        raise V4ContractError(f"observation value unusable: {raw}")

    def _validate_call_literals(self, capability_id: str, args: Mapping[str, str], query: str, observations: list[V4Observation]) -> None:
        safe_enum_fields = {"status"}
        source_derived_fields = {"assignee"}
        for key, value in args.items():
            raw = str(value).strip()
            if raw.startswith("$obs."):
                continue
            if key in safe_enum_fields:
                continue
            if key in source_derived_fields:
                # Canonical assignee must come from an observation, not planner invention.
                raise V4ContractError(f"{capability_id}.{key} must use a source observation reference")
            if key in {"reference", "space", "sprint_id", "release_id", "task_key", "product"} and not _literal_is_query_derived(raw, query):
                raise V4ContractError(f"planner literal is not grounded in user query: {key}={raw}")

    @classmethod
    def _compact_planner_value(cls, value: Any, *, field_name: str | None = None) -> Any:
        """Bound unstructured observation text without changing source truth.

        Planner observations are control-plane context, not the authoritative
        result payload.  Long descriptions/logs can hijack the next planning turn,
        so only known free-text fields are bounded.  Structured identity, task,
        sprint, status and count fields remain exact and untouched.
        """
        if isinstance(value, Mapping):
            return {
                str(key): cls._compact_planner_value(item, field_name=str(key))
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._compact_planner_value(item, field_name=field_name) for item in value]
        if (
            isinstance(value, str)
            and field_name is not None
            and field_name.casefold() in cls._PLANNER_UNSTRUCTURED_FIELDS
            and len(value) > cls._PLANNER_FREE_TEXT_LIMIT
        ):
            return value[: cls._PLANNER_FREE_TEXT_LIMIT].rstrip() + "…"
        return value

    @classmethod
    def _compact_data(cls, capability_id: str, data: Any) -> dict[str, Any]:
        if not isinstance(data, Mapping):
            return {"value": data}
        result = cls._compact_planner_value(dict(data))
        tasks = result.pop("tasks", None)
        if isinstance(tasks, list):
            keys = []
            for item in tasks:
                if isinstance(item, Mapping):
                    key = item.get("key") or item.get("source_id") or item.get("id")
                    if key:
                        keys.append(str(key))
            result.setdefault("count", len(tasks))
            result["task_keys_sample"] = keys[:20]
            result["task_key_count"] = len(keys)
        # Keep planner context compact even for assignees with thousands of rows.
        if isinstance(result.get("task_keys"), list):
            keys = [str(item) for item in result["task_keys"]]
            result["task_keys_sample"] = keys[:20]
            result["task_key_count"] = len(keys)
            result.pop("task_keys", None)
        result["capability"] = capability_id
        return result

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        started = time.perf_counter()
        trace_id = str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())
        query = str(request.query or "").strip()
        if not query:
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=trace_id, session_id=session_id, answer="Пустой запрос.", warnings=["query_empty"])

        loaded: list[str] = []
        observations: list[V4Observation] = []
        all_evidence: list[Evidence] = []
        full_results: list[dict[str, Any]] = []
        trajectory: list[dict[str, Any]] = []
        try:
            for planner_turn in range(self.planner.max_steps):
                decision = await self.planner.next_decision(
                    user_query=query,
                    catalog=self.catalog,
                    loaded_skills=tuple(loaded),
                    observations=observations,
                )
                trajectory.append({
                    "planner_turn": planner_turn + 1,
                    "decision": decision.kind,
                    "skill_id": decision.skill_id,
                    "capability_id": decision.capability_id,
                    "arguments": dict(decision.arguments or {}),
                    "rationale": decision.rationale,
                })

                if decision.kind == "load_skill":
                    skill_id = decision.skill_id or ""
                    if skill_id not in loaded:
                        self.catalog.load(skill_id)
                        loaded.append(skill_id)
                    continue

                if decision.kind == "ready":
                    if not observations:
                        return HarnessResponse(
                            status=ResponseStatus.NEEDS_CLARIFICATION,
                            trace_id=trace_id,
                            session_id=session_id,
                            question=decision.answer or "Уточните запрос.",
                            intent="skill_native_v4",
                            skill_id=loaded[-1] if loaded else None,
                            skill_version="4.0.0-poc" if loaded else None,
                            data={"_agent_core_v4": {"loaded_skills": loaded, "trajectory": trajectory, "semantic_prepass_used": False}},
                            warnings=["v4_ready_without_source_observation"],
                            latency_ms=(time.perf_counter() - started) * 1000,
                        )
                    try:
                        answer = await self.synthesizer.synthesize(query, observations)
                    except Exception:
                        answer = "\n".join(item.answer for item in observations if item.answer)
                    return HarnessResponse(
                        status=ResponseStatus.COMPLETED,
                        trace_id=trace_id,
                        session_id=session_id,
                        answer=answer,
                        intent="skill_native_v4",
                        skill_id=loaded[-1] if loaded else "skill-native-v4",
                        skill_version="4.0.0-poc",
                        data={
                            "_agent_core_v4": {
                                "runtime": "Agent Core v4",
                                "semantic_prepass_used": False,
                                "progressive_skill_loading": True,
                                "loaded_skills": loaded,
                                "trajectory": trajectory,
                                "observation_count": len(observations),
                            },
                            "results": full_results,
                        },
                        evidence=all_evidence,
                        warnings=[],
                        latency_ms=(time.perf_counter() - started) * 1000,
                    )

                capability_id = decision.capability_id or ""
                if capability_id not in self.catalog.allowed_capabilities(tuple(loaded)):
                    raise V4ContractError(f"capability not exposed by loaded skills: {capability_id}")
                if capability_id not in self._handlers:
                    raise V4ContractError(f"capability has no v4 handler: {capability_id}")
                raw_args = dict(decision.arguments or {})
                self._validate_call_literals(capability_id, raw_args, query, observations)
                resolved_args = {
                    key: self._resolve_observation_reference(value, observations)
                    for key, value in raw_args.items()
                }
                result = await self._handlers[capability_id](resolved_args)
                full_results.append({"step": len(observations) + 1, "capability_id": capability_id, "arguments": resolved_args, "answer": result.answer, "data": result.data})
                all_evidence.extend(result.evidence)
                observations.append(V4Observation(
                    step=len(observations) + 1,
                    capability_id=capability_id,
                    arguments=resolved_args,
                    answer=result.answer,
                    data=self._compact_data(capability_id, result.data),
                ))

            raise V4ContractError("v4 planner step budget exhausted without READY")

        except V4NeedsClarification as exc:
            return HarnessResponse(
                status=ResponseStatus.NEEDS_CLARIFICATION,
                trace_id=trace_id,
                session_id=session_id,
                question=exc.question,
                options=list(exc.options),
                intent="skill_native_v4",
                skill_id=loaded[-1] if loaded else None,
                skill_version="4.0.0-poc" if loaded else None,
                data={"_agent_core_v4": {"runtime": "Agent Core v4", "semantic_prepass_used": False, "loaded_skills": loaded, "trajectory": trajectory}},
                evidence=all_evidence,
                warnings=["v4_capability_clarification"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except AS21SourceUnavailable:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace_id,
                session_id=session_id,
                answer="Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат.",
                intent="skill_native_v4",
                data={"_agent_core_v4": {"loaded_skills": loaded, "trajectory": trajectory, "semantic_prepass_used": False}},
                warnings=["source_unavailable"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except AS21SourceError:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace_id,
                session_id=session_id,
                answer="Источник AS21 вернул некорректные данные.",
                intent="skill_native_v4",
                data={"_agent_core_v4": {"loaded_skills": loaded, "trajectory": trajectory, "semantic_prepass_used": False}},
                warnings=["source_protocol_error"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as exc:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace_id,
                session_id=session_id,
                answer="Agent Core v4 не смог безопасно завершить траекторию.",
                intent="skill_native_v4",
                data={"_agent_core_v4": {"loaded_skills": loaded, "trajectory": trajectory, "semantic_prepass_used": False, "exception_type": type(exc).__name__, "error": str(exc)}},
                warnings=["v4_runtime_failure"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )