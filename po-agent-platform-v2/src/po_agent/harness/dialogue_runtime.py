"""Dialogue-first Harness orchestration.

Natural-language understanding is separated from deterministic capabilities.
The LLM may interpret wording and propose a semantic frame, but source entity
identifiers and business semantics are grounded before execution. Uncertainty
becomes an explicit clarification turn instead of a silent guess.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol, Any

from po_agent.adapters.task_api import AS21CapabilityUnavailable, AS21SourceError, AS21SourceUnavailable
from po_agent.llm.client import LLMClient, LLMMessage

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .learned_semantics import LearnedSemanticsStore, LearnedSemanticRule
from .skill_catalog import SKILL_CATALOG, canonical_semantic_intents, intent_to_skill_id


def _refine_skill_id_by_slots(skill_id: str, slots: dict[str, str]) -> str:
    if skill_id != "task-search":
        return skill_id
    if slots.get("assignee") or slots.get("member_login"):
        return "task-search-assignee"
    if slots.get("sprint_id"):
        return "task-search-sprint"
    if slots.get("release_id"):
        return "task-search-release"
    if slots.get("status"):
        return "task-search-status"
    if slots.get("product"):
        return "task-search-product"
    return "task-search"


def _extract_explicit_task_key(query: str) -> str | None:
    """Extract exactly one explicit task key from the original user query."""
    matches = re.findall(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+(?![-A-ZА-Я0-9_])\b", query, re.I)
    return matches[0] if len(matches) == 1 else None


def _semantic_capability_contract() -> tuple[list[str], list[dict[str, str]]]:
    """Build the LLM semantic contract from the executable Skill Catalog.

    The catalog remains the single source of truth. The interpreter sees only
    implemented skills and their canonical semantic labels; execution still
    resolves those labels deterministically through ``intent_to_skill_id``.
    """
    allowed_intents = list(canonical_semantic_intents())
    available_capabilities = [
        {
            "intent": entry.id.replace("-", "_"),
            "skill_id": entry.id,
            "capability_id": entry.capability_id,
            "domain": entry.domain,
            "description": entry.description,
        }
        for entry in SKILL_CATALOG
        if entry.status == "implemented"
    ]
    return allowed_intents, available_capabilities


@dataclass(frozen=True)
class ClarificationNeed:
    field: str
    question: str
    options: tuple[str, ...] = ()


@dataclass
class SemanticFrame:
    canonical_query: str
    intent_hint: str | None = None
    slots: dict[str, str] = field(default_factory=dict)
    clarifications: list[ClarificationNeed] = field(default_factory=list)
    confidence: float = 1.0
    llm_used: bool = False


class SemanticInterpreter(Protocol):
    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame: ...


class SemanticGrounder(Protocol):
    async def semantic_context(self) -> dict[str, Any]: ...
    async def ground(self, frame: SemanticFrame, original_query: str) -> SemanticFrame: ...


class LLMJsonSemanticInterpreter:
    """Strict JSON semantic interpreter suitable for Qwen/Qwen-Coder models."""

    SYSTEM = """You are the semantic interpreter of a PO Harness agent.
Return JSON only with keys canonical_query, intent_hint, slots, clarifications, confidence.
clarifications is an array of {field, question, options}.
Use placeholders {task_key}, {member_login}, {sprint_id}, {release_id}, {status} when a grounded value is not yet known.
Useful slots: task_raw, task_key, person_raw, member_login, sprint_raw, sprint_id, release_raw, release_id, status_raw, status_semantic, product, phrase, learn_term, learn_meaning, learn_scope.

The user payload context contains:
- allowed_intents: the complete canonical semantic vocabulary for currently implemented skills.
- available_capabilities: metadata for those implemented skills.
For a supported request, intent_hint MUST be exactly one value from allowed_intents.
If the request is genuinely unsupported by available_capabilities, set intent_hint to null.
Never invent a new intent label and never choose a capability that is not present in the supplied contract.

Capability selection policy:
- First identify the semantic domain and requested outcome, then compare the capabilities in that domain by meaning, not by literal wording or intent name.
- Treat a request as supported when an available capability can produce the requested outcome, even if the user's wording differs from the catalog description.
- Missing or unresolved source identifiers/slots do NOT make a supported request unsupported. Select the capability first, preserve raw entity wording in slots, and use grounding or clarification for unresolved values.
- Use intent_hint=null only when no available capability can satisfy the requested operation after semantic comparison. Do not use null merely because a required slot is missing, wording is indirect, or confidence in an entity match is low.
- If several capabilities in the same domain are plausible, choose the most specific capability matching the requested outcome. If the ambiguity is about an entity or slot rather than the operation, keep the selected intent and request clarification for that slot.

Rules:
1. Understand free-form Russian/English wording, names, grammatical cases and shorthand.
2. NEVER invent task IDs, sprint IDs, release IDs, logins, statuses or source facts.
3. If an entity or business term is ambiguous, add a clarification instead of guessing.
4. canonical_query must preserve the requested operation and only use values explicitly supplied or resolved in context.
5. Do not calculate metrics; deterministic capabilities do that after interpretation.
6. For business concepts such as 'open tasks', use a learned semantic rule only if it exists; otherwise set status_semantic and leave {status} unresolved.
7. team_members, known_tasks, known_sprints, known_releases and known_statuses are source-backed candidates. Use them only when the match is unambiguous.
8. Learned semantics are configuration facts supplied by the Harness; do not extend them by analogy.
9. For multi-filter task searches use the canonical task_search intent and put each filter in slots. The Harness executes all filters deterministically.
10. When the user explicitly supplies a task key such as OLP-3134 or DMS-341, copy that exact source identifier into slots.task_key. Do not rewrite, infer, or generate task keys. For task lookup/details use the canonical task_lookup intent; for assignee/team matching preserve the same task_key in slots and choose the matching canonical team intent from allowed_intents.
11. Only if the user explicitly asks to remember a reusable definition (for example 'always treat open tasks as all unresolved'), set intent_hint=learn_semantic and slots learn_term, learn_meaning, optionally learn_scope. Prefer canonical learn_meaning values such as not_completed or a comma-separated list of explicit statuses.
"""

    DOMAIN_CANDIDATE_SYSTEM = """You are a semantic candidate ranker for PO Harness domains.
Return JSON only: {\"domain\": <exactly one supplied domain>, \"confidence\": <0..1>}.
Candidate ranking is NOT authorization. When two candidates are supplied, compare only those two and return the one whose business object and requested outcome are semantically closer to the user request. Never return null; authorization happens later.
"""

    CAPABILITY_CANDIDATE_SYSTEM = """You are a semantic candidate ranker for capabilities inside one selected PO Harness domain.
Return JSON only: {\"intent_hint\": <exactly one supplied canonical intent>, \"confidence\": <0..1>}.
Candidate ranking is NOT authorization. When two candidates are supplied, compare only those two and return the one whose operation/outcome is semantically closer to the user request. Never return null; authorization happens later.
"""

    SEMANTIC_ENTAILMENT_SYSTEM = """You are the fail-closed semantic authorization gate for a PO Harness.
You receive exactly one user query and exactly one selected catalog capability.
Evaluate four independent conditions:
1. business_object_match: the business object requested by the user is inside the selected capability's domain/scope.
2. operation_match: the operation the user asks to perform is the operation implemented by the capability.
3. outcome_match: the result/outcome the user wants can be directly produced by the capability.
4. supported: true only if ALL three matches above are true.

Be strict about business scope. A search capability searches only the catalog business object it is defined for; generic words such as "find", "show", or "search" do not authorize unrelated information. A task capability cannot answer weather, arithmetic, general chit-chat, code-generation, office-duty, or other non-task requests merely because text could theoretically be searched. Likewise, a sprint, release, team, portfolio, or PO capability is limited to its declared catalog scope.

Do NOT evaluate whether IDs, people, sprints, releases, or other source entities exist; grounding handles that later. Missing source slots must not make an otherwise matching operation unsupported.
Do NOT choose another capability. Do NOT broaden the selected capability by analogy. If any of business object, operation, or requested outcome is outside the selected capability contract, return the corresponding match as false and supported=false. When uncertain, fail closed.
"""

    CANDIDATE_CONTRACT_REPAIR = """Your previous candidate response violated the ranking contract. You MUST return exactly one value from the supplied non-empty candidate set. Candidate ranking is not authorization, so uncertainty or an unsupported request is not a reason to return null. Return JSON only."""

    def __init__(self, client: LLMClient, *, model: str | None = None) -> None:
        self.client = client
        self.model = model

    @staticmethod
    def _parse_json_content(raw: str) -> dict[str, Any] | None:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S)
        try:
            data = json.loads(text)
        except Exception:
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _domain_signatures(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        domains: dict[str, dict[str, Any]] = {}
        for item in capabilities:
            domain = str(item.get("domain") or "").strip()
            if not domain:
                continue
            signature = domains.setdefault(domain, {"domain": domain, "intents": [], "capability_descriptions": []})
            if item.get("intent"):
                signature["intents"].append(str(item["intent"]))
            if item.get("description"):
                signature["capability_descriptions"].append(str(item["description"]))
        return [domains[name] for name in sorted(domains)]

    @staticmethod
    def _closed_set_response_format(key: str, allowed: list[str]) -> dict[str, Any]:
        """Build a provider-level JSON-schema enum from the catalog-derived candidate set."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": f"po_harness_{key}_choice",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        key: {"type": "string", "enum": allowed},
                        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    },
                    "required": [key, "confidence"],
                    "additionalProperties": False,
                },
            },
        }

    @staticmethod
    def _entailment_response_format() -> dict[str, Any]:
        """Require an explicit scope/operation/outcome authorization decision."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "po_harness_semantic_entailment",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "business_object_match": {"type": "boolean"},
                        "operation_match": {"type": "boolean"},
                        "outcome_match": {"type": "boolean"},
                        "supported": {"type": "boolean"},
                        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    },
                    "required": [
                        "business_object_match",
                        "operation_match",
                        "outcome_match",
                        "supported",
                        "confidence",
                    ],
                    "additionalProperties": False,
                },
            },
        }

    async def _required_choice(self, system: str, payload: str, key: str, allowed: list[str], max_tokens: int) -> str | None:
        if not allowed:
            return None
        response_format = self._closed_set_response_format(key, allowed)
        for repair in (False, True):
            messages = [LLMMessage(role="system", content=system)]
            if repair:
                messages.append(LLMMessage(role="system", content=self.CANDIDATE_CONTRACT_REPAIR))
            messages.append(LLMMessage(role="user", content=payload))
            try:
                response = await self.client.complete(
                    messages,
                    model=self.model,
                    temperature=0.0,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
                if not response.choices:
                    continue
                data = self._parse_json_content(response.choices[0].message.content)
                candidate = data.get(key) if data else None
                candidate = str(candidate).strip() if candidate else None
                if candidate in allowed:
                    return candidate
            except Exception:
                continue
        return None

    async def _pairwise_tournament(
        self,
        *,
        query: str,
        system: str,
        key: str,
        candidates: list[str],
        details: dict[str, dict[str, Any]],
        max_tokens: int,
    ) -> str | None:
        """Aggregate pairwise semantic evidence without letting one null kill recovery.

        Every unique pair is compared once. A valid winner earns one point;
        unresolved/provider-failed pairs contribute no score and do not abort the
        remaining comparisons. The result is accepted only when there is a unique
        top scorer with at least one valid win. A tie or zero evidence fails closed.
        This makes recovery order-independent while leaving authorization to the
        mandatory entailment gate that runs after candidate selection.
        """
        unique = list(dict.fromkeys(candidate for candidate in candidates if candidate))
        if not unique:
            return None
        if len(unique) == 1:
            return unique[0]

        scores = {candidate: 0 for candidate in unique}
        valid_comparisons = 0
        for left_index, first in enumerate(unique[:-1]):
            for second in unique[left_index + 1:]:
                pair = [first, second]
                payload = json.dumps(
                    {
                        "query": query,
                        "candidate_pair": pair,
                        "candidate_details": [details.get(item, {"value": item}) for item in pair],
                    },
                    ensure_ascii=False,
                )
                winner = await self._required_choice(system, payload, key, pair, max_tokens)
                if winner is None:
                    continue
                scores[winner] += 1
                valid_comparisons += 1

        if valid_comparisons == 0:
            return None
        best_score = max(scores.values())
        if best_score <= 0:
            return None
        leaders = [candidate for candidate, score in scores.items() if score == best_score]
        return leaders[0] if len(leaders) == 1 else None

    async def _select_domain_candidate(self, query: str, capabilities: list[dict[str, Any]]) -> str | None:
        signatures = self._domain_signatures(capabilities)
        domains = [str(item["domain"]) for item in signatures]
        details = {str(item["domain"]): item for item in signatures}
        return await self._pairwise_tournament(
            query=query,
            system=self.DOMAIN_CANDIDATE_SYSTEM,
            key="domain",
            candidates=domains,
            details=details,
            max_tokens=120,
        )

    async def _select_capability_candidate(self, query: str, domain: str, allowed: list[str], capabilities: list[dict[str, Any]]) -> str | None:
        domain_capabilities = [item for item in capabilities if str(item.get("domain")) == domain]
        domain_intents = [str(item.get("intent")) for item in domain_capabilities if item.get("intent") in allowed]
        details = {str(item.get("intent")): item for item in domain_capabilities if item.get("intent") in domain_intents}
        return await self._pairwise_tournament(
            query=query,
            system=self.CAPABILITY_CANDIDATE_SYSTEM,
            key="intent_hint",
            candidates=domain_intents,
            details=details,
            max_tokens=140,
        )

    @staticmethod
    def _canonical_capability_for_intent(intent: str, allowed: list[str], capabilities: list[dict[str, Any]]) -> tuple[str, dict[str, Any]] | None:
        normalized = intent.strip().replace("-", "_").replace(" ", "_").casefold()
        if normalized in allowed:
            selected = next((item for item in capabilities if str(item.get("intent")) == normalized), None)
            return (normalized, selected) if selected is not None else None
        skill_id = intent_to_skill_id(normalized)
        if skill_id is None:
            return None
        selected = next((item for item in capabilities if str(item.get("skill_id")) == skill_id), None)
        if selected is None:
            return None
        canonical = str(selected.get("intent") or "")
        return (canonical, selected) if canonical in allowed else None

    async def _semantic_entails_capability(self, query: str, intent: str, capabilities: list[dict[str, Any]]) -> bool:
        selected = next((item for item in capabilities if str(item.get("intent")) == intent), None)
        if selected is None:
            return False
        payload = json.dumps(
            {
                "query": query,
                "selected_capability_contract": {
                    "intent": selected.get("intent"),
                    "domain": selected.get("domain"),
                    "capability_id": selected.get("capability_id"),
                    "description": selected.get("description"),
                },
            },
            ensure_ascii=False,
        )
        try:
            response = await self.client.complete(
                [
                    LLMMessage(role="system", content=self.SEMANTIC_ENTAILMENT_SYSTEM),
                    LLMMessage(role="user", content=payload),
                ],
                model=self.model,
                temperature=0.0,
                max_tokens=160,
                response_format=self._entailment_response_format(),
            )
            if not response.choices:
                return False
            data = self._parse_json_content(response.choices[0].message.content)
            if data is None:
                return False
            return bool(
                data.get("business_object_match") is True
                and data.get("operation_match") is True
                and data.get("outcome_match") is True
                and data.get("supported") is True
            )
        except Exception:
            return False

    async def _repair_missing_intent(self, query: str, context: dict[str, Any]) -> str | None:
        allowed = [str(x) for x in context.get("allowed_intents", []) if x]
        capabilities = [item for item in context.get("available_capabilities", []) if isinstance(item, dict)]
        domain = await self._select_domain_candidate(query, capabilities)
        if domain is None:
            return None
        intent = await self._select_capability_candidate(query, domain, allowed, capabilities)
        if intent is None:
            return None
        return intent if await self._semantic_entails_capability(query, intent, capabilities) else None

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        semantic_context = context or {}
        payload = json.dumps({"query": query, "context": semantic_context}, ensure_ascii=False)
        response = await self.client.complete(
            [LLMMessage(role="system", content=self.SYSTEM), LLMMessage(role="user", content=payload)],
            model=self.model,
            temperature=0.0,
            max_tokens=900,
        )
        if not response.choices:
            raise ValueError("semantic interpreter returned no choices")
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I | re.S)
        data = json.loads(raw)
        if not isinstance(data, dict) or not isinstance(data.get("canonical_query"), str):
            raise ValueError("semantic interpreter contract violation")

        allowed = [str(x) for x in semantic_context.get("allowed_intents", []) if x]
        capabilities = [item for item in semantic_context.get("available_capabilities", []) if isinstance(item, dict)]
        original_intent = str(data.get("intent_hint") or "").strip()
        semantic_rejected = False

        if original_intent and original_intent.strip().casefold() == "learn_semantic":
            data["intent_hint"] = "learn_semantic"
        elif original_intent:
            resolved = self._canonical_capability_for_intent(original_intent, allowed, capabilities)
            if resolved is None:
                data["intent_hint"] = None
                semantic_rejected = True
            else:
                canonical_intent, _ = resolved
                if await self._semantic_entails_capability(query, canonical_intent, capabilities):
                    data["intent_hint"] = canonical_intent
                else:
                    data["intent_hint"] = None
                    semantic_rejected = True
        else:
            repaired_intent = await self._repair_missing_intent(query, semantic_context)
            if repaired_intent:
                data["intent_hint"] = repaired_intent
            else:
                semantic_rejected = True

        needs = []
        for item in data.get("clarifications", []) or []:
            if isinstance(item, dict) and item.get("field") and item.get("question"):
                needs.append(ClarificationNeed(str(item["field"]), str(item["question"]), tuple(str(x) for x in item.get("options", []) if x)))
        if semantic_rejected and not needs:
            needs.append(ClarificationNeed("intent", "Я не нашёл поддерживаемую операцию для этого запроса. Уточните, что вы хотите получить в рамках возможностей PO Agent."))
        try:
            confidence = float(data.get("confidence", 1.0))
        except (TypeError, ValueError):
            confidence = 0.0
        return SemanticFrame(
            data["canonical_query"].strip() or query,
            str(data.get("intent_hint")) if data.get("intent_hint") else None,
            {str(k): str(v) for k, v in (data.get("slots") or {}).items() if v is not None},
            needs,
            max(0.0, min(1.0, confidence)),
            True,
        )


class ConservativeSemanticInterpreter:
    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        text = query.strip()
        low = text.casefold()
        if "истор" in low and re.search(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b", text, re.I):
            key = re.search(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b", text, re.I).group(0)
            text = f"история {key}"
        return SemanticFrame(canonical_query=text, confidence=0.7, llm_used=False)


@dataclass
class _PendingDialogue:
    frame: SemanticFrame
    remaining: list[ClarificationNeed]
    answers: dict[str, str] = field(default_factory=dict)


class DialogueHarnessRuntime:
    def __init__(
        self,
        inner,
        interpreter: SemanticInterpreter | None = None,
        semantics: LearnedSemanticsStore | None = None,
        grounder: SemanticGrounder | None = None,
    ) -> None:
        self.inner = inner
        self.interpreter = interpreter or ConservativeSemanticInterpreter()
        self.semantics = semantics
        self.grounder = grounder
        self._pending = {}
        for name in ("adapter", "router", "capabilities", "skills"):
            setattr(self, name, getattr(inner, name))

    @staticmethod
    def _clarification_response(session, pending):
        need = pending.remaining[0]
        return HarnessResponse(
            status=ResponseStatus.NEEDS_CLARIFICATION,
            trace_id=str(uuid.uuid4()),
            session_id=session,
            question=need.question,
            options=list(need.options),
            clarification_id=f"{session}:{need.field}",
            data={
                "missing_field": need.field,
                "semantic_frame": dict(pending.frame.slots),
                "_harness": {"llm_used": pending.frame.llm_used, "dialogue_state": "clarifying"},
            },
            warnings=["clarification_required"],
        )

    @staticmethod
    def _apply_answers(frame, answers):
        query = frame.canonical_query
        slots = dict(frame.slots)
        for field, value in answers.items():
            slots[field] = value
            token = "{" + field + "}"
            if token in query:
                query = query.replace(token, value)
            elif value and value.casefold() not in query.casefold():
                query = f"{query} {value}"
        return SemanticFrame(query, frame.intent_hint, slots, [], frame.confidence, frame.llm_used)

    def learn_explicit_definition(self, *, term, meaning, trace_id, scope="global"):
        if self.semantics is None:
            raise RuntimeError("learned semantics store is not configured")
        return self.semantics.learn_explicit_definition(
            term=term,
            meaning=meaning,
            source_trace_id=trace_id,
            scope=scope,
        )

    _EXECUTION_SLOT_KEYS = {
        "task_key", "sprint_id", "release_id", "product", "assignee", "status",
        "phrase", "attachment_type", "threshold_days", "capacity_hours", "subject",
    }
    _TASK_SEARCH_SKILL_IDS = {
        "task-search", "task-search-assignee", "task-search-status",
        "task-search-sprint", "task-search-release", "task-search-product",
    }
    _REQUIRED_ARGS_BY_CAPABILITY = {
        "task.lookup": ("task_key",), "task.summary": ("task_key",), "task.quality": ("task_key",),
        "task.missing_requirements": ("task_key",), "task.acceptance_analysis": ("task_key",),
        "task.dependencies": ("task_key",), "task.blockers": ("task_key",), "task.similar": ("task_key",),
        "task.history": ("task_key",), "task.time_in_status": ("task_key",),
        "sprint.health": ("sprint_id",), "sprint.velocity": ("sprint_id",), "sprint.throughput": ("sprint_id",),
        "sprint.wip": ("sprint_id",), "release.health": ("release_id",), "release.scope": ("release_id",),
        "release.progress": ("release_id",), "release.blockers": ("release_id",),
        "release.dependencies": ("release_id",), "release.risk_queue": ("release_id",),
        "team.competency_match": ("task_key",), "team.assignee_recommendation": ("task_key",),
    }

    @staticmethod
    def _build_capability_args(frame):
        slots = {str(k): str(v) for k, v in frame.slots.items() if v not in (None, "")}
        args = {k: v for k, v in slots.items() if k in DialogueHarnessRuntime._EXECUTION_SLOT_KEYS}
        if "task_key" not in args and slots.get("task_id"):
            args["task_key"] = slots["task_id"]
        if "task_key" not in args and slots.get("issue_key"):
            args["task_key"] = slots["issue_key"]
        if "assignee" not in args and slots.get("member_login"):
            args["assignee"] = slots["member_login"]
        return args

    def _validate_required_args(self, capability_id, args):
        missing = [arg for arg in self._REQUIRED_ARGS_BY_CAPABILITY.get(capability_id, ()) if not args.get(arg)]
        return (not missing, None if not missing else f"Missing required slot: {', '.join(missing)}")

    async def _validate_source_backed_sprint(self, sprint_id: str) -> bool:
        """Re-prove a sprint selector at the final execution boundary.

        Grounding is the primary entity-validation layer, but execution must not
        depend on every upstream wrapper preserving that decision perfectly.  A
        production adapter that exposes ``sprint_exists`` provides the final
        fail-closed source check.  Fake/frozen adapters without that contract
        retain their existing behavior.
        """
        validator = getattr(self.adapter, "sprint_exists", None)
        if not callable(validator):
            return True
        return bool(await validator(sprint_id))

    @staticmethod
    def _enrich_explicit_task_key(frame: SemanticFrame, original_query: str) -> SemanticFrame:
        if frame.slots.get("task_key"):
            return frame
        task_key = _extract_explicit_task_key(original_query)
        if task_key is None:
            return frame
        new_slots = dict(frame.slots)
        new_slots["task_key"] = task_key
        return SemanticFrame(frame.canonical_query, frame.intent_hint, new_slots, frame.clarifications, frame.confidence, frame.llm_used)

    @staticmethod
    def _source_failure(session, warning, answer, started, *, data=None):
        return HarnessResponse(status=ResponseStatus.FAILED, trace_id=str(uuid.uuid4()), session_id=session, answer=answer, data=data, warnings=[warning], latency_ms=(time.perf_counter() - started) * 1000)

    def _missing_required_source_fact(self, query):
        required_fact = getattr(self.inner, "_required_fact", None)
        source_facts = getattr(self.inner, "source_facts", None)
        if not callable(required_fact) or source_facts is None:
            return None
        required = required_fact(query)
        return required if required and required not in source_facts else None

    async def _execute_frame(self, frame, session, started):
        hint = (frame.intent_hint or "").strip().replace("-", "_").replace(" ", "_").casefold()
        if hint == "learn_semantic":
            if self.semantics is None:
                return self._source_failure(session, "learning_store_unavailable", "Хранилище обучаемой конфигурации недоступно.", started)
            term = (frame.slots.get("learn_term") or "").strip()
            meaning = (frame.slots.get("learn_meaning") or "").strip()
            scope = (frame.slots.get("learn_scope") or "global").strip()
            if not term or not meaning:
                pending = _PendingDialogue(frame, [ClarificationNeed("learn_meaning", "Какое точное правило вы хотите запомнить?")])
                self._pending[session] = pending
                return self._clarification_response(session, pending)
            trace = str(uuid.uuid4())
            rule = self.semantics.learn_explicit_definition(term=term, meaning=meaning, source_trace_id=trace, scope=scope)
            response = HarnessResponse(status=ResponseStatus.COMPLETED, trace_id=trace, session_id=session, answer=(f"Запомнил правило «{rule.term}» = «{rule.meaning}»." if rule.status == "active" else "Новое правило конфликтует с уже активным. Я сохранил его как candidate и не изменил текущее поведение."), data={"learning_rule": {"id": rule.rule_id, "term": rule.term, "meaning": rule.meaning, "scope": rule.scope, "version": rule.version, "status": rule.status}}, warnings=[] if rule.status == "active" else ["learning_conflict_pending"], latency_ms=(time.perf_counter() - started) * 1000)
            self._decorate(response, frame.llm_used)
            return response
        if hint == "":
            response = await self.inner.process(HarnessRequest(query=frame.canonical_query, session_id=session))
            self._decorate(response, frame.llm_used)
            return response
        skill_id = intent_to_skill_id(hint)
        if skill_id is None:
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=str(uuid.uuid4()), session_id=session, answer="Интент не распознан или нереализован.", intent=hint, warnings=["unsupported_semantic_intent"], latency_ms=(time.perf_counter() - started) * 1000)
        capability_args = self._build_capability_args(frame)
        refined = self._refine_skill_id_by_slots(skill_id, frame.slots)
        sprint_id = capability_args.get("sprint_id")
        if sprint_id:
            try:
                sprint_proven = await self._validate_source_backed_sprint(sprint_id)
            except AS21CapabilityUnavailable:
                return self._source_failure(session, "source_capability_unavailable", "Источник AS21 не предоставляет данные для проверки спринта.", started)
            except AS21SourceUnavailable:
                return self._source_failure(session, "source_unavailable", "Источник AS21 временно недоступен. Нельзя подтвердить спринт.", started)
            except AS21SourceError:
                return self._source_failure(session, "source_protocol_error", "Источник AS21 вернул некорректные данные при проверке спринта.", started)
            if not sprint_proven:
                return HarnessResponse(
                    status=ResponseStatus.NEEDS_CLARIFICATION,
                    trace_id=str(uuid.uuid4()),
                    session_id=session,
                    question=f"Не могу подтвердить спринт «{sprint_id}» по данным AS21. Уточните спринт.",
                    data={"sprint_id": sprint_id, "source_proven": False},
                    warnings=["unproven_sprint"],
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
        try:
            skill = self.skills.resolve_by_id(refined)
        except ValueError:
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=str(uuid.uuid4()), session_id=session, answer="Навык не найден или недоступен.", intent=hint, skill_id=refined, warnings=["semantic_skill_unavailable"], latency_ms=(time.perf_counter() - started) * 1000)
        valid, error = self._validate_required_args(skill.capability_id, capability_args)
        if not valid:
            return HarnessResponse(status=ResponseStatus.NEEDS_CLARIFICATION, trace_id=str(uuid.uuid4()), session_id=session, question=f"Мне не хватает информации: {error}.", warnings=["semantic_slot_missing"], latency_ms=(time.perf_counter() - started) * 1000)
        try:
            if refined in self._TASK_SEARCH_SKILL_IDS and sum(1 for k in ["assignee", "sprint_id", "release_id", "status", "product"] if k in capability_args) >= 2:
                result = await self.capabilities.execute("task.search.composite", capability_args)
            else:
                result = await self.capabilities.execute(skill.capability_id, capability_args)
            response = HarnessResponse(status=ResponseStatus.COMPLETED, trace_id=str(uuid.uuid4()), session_id=session, answer=result.answer, intent=hint, skill_id=skill.id, skill_version=skill.version, data=result.data, evidence=result.evidence, warnings=result.warnings, latency_ms=(time.perf_counter() - started) * 1000)
            self._decorate(response, frame.llm_used)
            return response
        except AS21CapabilityUnavailable:
            return self._source_failure(session, "source_capability_unavailable", "Источник AS21 не предоставляет данные, необходимые для этого запроса.", started)
        except AS21SourceUnavailable:
            return self._source_failure(session, "source_unavailable", "Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат.", started)
        except AS21SourceError:
            return self._source_failure(session, "source_protocol_error", "Источник AS21 вернул некорректные данные.", started)

    @staticmethod
    def _refine_skill_id_by_slots(skill_id, slots):
        return _refine_skill_id_by_slots(skill_id, slots)

    async def process(self, request):
        session = request.session_id or str(uuid.uuid4())
        started = time.perf_counter()
        if not request.query or not request.query.strip():
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=str(uuid.uuid4()), session_id=session, answer="Запрос пуст. Пожалуйста, уточните, что вы хотите получить.", data=None, warnings=["query_empty"], latency_ms=(time.perf_counter() - started) * 1000)
        if session in self._pending:
            pending = self._pending[session]
            need = pending.remaining.pop(0)
            answer = request.query.strip()
            if not answer:
                pending.remaining.insert(0, need)
                return self._clarification_response(session, pending)
            pending.answers[need.field] = answer
            pending.frame.slots[need.field] = answer
            if pending.remaining:
                return self._clarification_response(session, pending)
            self._pending.pop(session, None)
            return await self._execute_frame(self._apply_answers(pending.frame, pending.answers), session, started)
        missing_fact = self._missing_required_source_fact(request.query)
        if missing_fact:
            return self._source_failure(session, "source_capability_unavailable", f"Источник AS21 не предоставляет обязательные данные для этого запроса: {missing_fact}.", started, data={"missing_source_fact": missing_fact})

        allowed_intents, available_capabilities = _semantic_capability_contract()
        semantic_context = {"session_id": session, "allowed_intents": allowed_intents, "available_capabilities": available_capabilities}
        if self.semantics is not None:
            semantic_context["learned_semantics"] = self.semantics.context("global")
        if self.grounder is not None:
            try:
                semantic_context.update(await self.grounder.semantic_context())
            except AS21CapabilityUnavailable:
                return self._source_failure(session, "source_capability_unavailable", "Источник AS21 не предоставляет данные для проверки контекста запроса.", started)
            except AS21SourceUnavailable:
                return self._source_failure(session, "source_unavailable", "Источник AS21 временно недоступен. Нельзя безопасно интерпретировать запрос без проверки источника.", started)
            except AS21SourceError:
                return self._source_failure(session, "source_protocol_error", "Источник AS21 вернул некорректные данные при проверке контекста.", started)
        try:
            frame = await self.interpreter.interpret(request.query, context=semantic_context)
        except Exception:
            return self._source_failure(session, "semantic_interpretation_failure", "Не удалось безопасно интерпретировать запрос. Попробуйте переформулировать его.", started)

        frame = self._enrich_explicit_task_key(frame, request.query)
        if frame.confidence < 0.45 and not frame.clarifications:
            frame.clarifications.append(ClarificationNeed("intent", "Я не уверен, что правильно понял запрос. Что именно вы хотите получить?"))
        if self.grounder is not None and (frame.intent_hint or "").strip().casefold() != "learn_semantic":
            try:
                frame = await self.grounder.ground(frame, request.query)
            except AS21CapabilityUnavailable:
                return self._source_failure(session, "source_capability_unavailable", "Источник AS21 не предоставляет данные для проверки сущностей запроса.", started)
            except AS21SourceUnavailable:
                return self._source_failure(session, "source_unavailable", "Источник AS21 временно недоступен. Нельзя подтвердить сущности запроса.", started)
            except AS21SourceError:
                return self._source_failure(session, "source_protocol_error", "Источник AS21 вернул некорректные данные при проверке сущностей.", started)
        if frame.clarifications:
            pending = _PendingDialogue(frame, list(frame.clarifications))
            self._pending[session] = pending
            return self._clarification_response(session, pending)
        return await self._execute_frame(frame, session, started)

    @staticmethod
    def _decorate(response, llm_used):
        if response.data is None:
            response.data = {}
        if isinstance(response.data, dict):
            meta = response.data.setdefault("_harness", {})
            if isinstance(meta, dict):
                meta["llm_used"] = llm_used
                meta["dialogue_state"] = "answered"
                meta["feedback_prompt"] = "Ответ помог? Что бы вы хотели улучшить?"
