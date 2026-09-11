"""Provider-robust decision protocol for Agent Core v4.

The V4 planner remains fully agentic: the LLM chooses which skill to load and
which governed capability to call next.  This module only hardens the transport
of that decision so a provider-specific malformed JSON serialization cannot kill
an otherwise valid multi-step trajectory.

JSON remains the primary protocol.  When serialization is unreliable, the model
may use a tiny typed DSL that is decoded into the same V4Decision contract:

    LOAD <skill_id>
    CALL <capability_id> key=value key2="multi word value"
    READY <short answer/synthesis instruction>

The DSL does not bypass capability loading, observation binding, source-backed
identity checks, argument validation or postconditions.  It is deliberately
trajectory-agnostic and contains no person/space/sprint/task rules.
"""
from __future__ import annotations

import json
import re
import shlex
from types import SimpleNamespace
from typing import Any, Mapping

from po_agent.llm.client import LLMMessage

from .agent_core_v4 import (
    SkillCatalogV4,
    SkillNativePlannerV4,
    V4ContractError,
    V4Decision,
    V4Observation,
    _extract_json_object,
)
from .agent_core_v4_reliable import ReliableAgentCoreV4Runtime


class RobustSkillNativePlannerV4(SkillNativePlannerV4):
    """Skill-native planner with JSON primary + typed DSL recovery."""

    DSL_SYSTEM_ADDENDUM = """
Decision transport reliability:
- JSON is preferred.
- If you cannot serialize the required JSON object exactly, return exactly ONE DSL line instead:
  LOAD <skill_id>
  CALL <capability_id> key=value key2="multi word value"
  READY <short answer or synthesis instruction>
- DSL is only an alternate serialization of the same decision. It does not relax tool, source, identity, observation or safety constraints.
"""

    DSL_REPAIR = """The previous decision could not be decoded safely.
Return exactly ONE decision. Prefer valid JSON. If JSON serialization is unreliable, return exactly one DSL line:
LOAD <skill_id>
CALL <capability_id> key=value key2="multi word value"
READY <short answer>
Do not add prose, markdown or source facts. Do not invent ids."""

    @staticmethod
    def _clean_text(raw: str) -> str:
        text = str(raw or "").strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.I | re.S).strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:text|json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
        return text

    @classmethod
    def _decode_dsl(cls, raw: str) -> V4Decision | None:
        text = cls._clean_text(raw)
        if not text:
            return None
        candidate_lines = [
            line.strip()
            for line in text.splitlines()
            if re.match(r"^(?:LOAD|CALL|READY)\b", line.strip(), flags=re.I)
        ]
        if len(candidate_lines) != 1:
            return None
        line = candidate_lines[0]
        try:
            parts = shlex.split(line, posix=True)
        except ValueError:
            return None
        if not parts:
            return None
        command = parts[0].upper()
        if command == "LOAD":
            if len(parts) != 2 or not parts[1].strip():
                return None
            return V4Decision("load_skill", skill_id=parts[1].strip(), rationale="dsl_recovery")
        if command == "CALL":
            if len(parts) < 2 or not parts[1].strip():
                return None
            arguments: dict[str, str] = {}
            for token in parts[2:]:
                if "=" not in token:
                    return None
                key, value = token.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", key) or not value:
                    return None
                arguments[key] = value
            return V4Decision(
                "call",
                capability_id=parts[1].strip(),
                arguments=arguments,
                rationale="dsl_recovery",
            )
        if command == "READY":
            answer = line[len(parts[0]):].strip()
            return V4Decision("ready", answer=answer, rationale="dsl_recovery") if answer else None
        return None

    @classmethod
    def _decode_any(cls, raw: str) -> V4Decision | None:
        obj = _extract_json_object(raw)
        decision = cls._decode(obj) if obj is not None else None
        return decision or cls._decode_dsl(raw)

    @staticmethod
    def _decision_allowed(
        decision: V4Decision,
        *,
        catalog: SkillCatalogV4,
        loaded_skills: tuple[str, ...],
    ) -> tuple[bool, str | None]:
        if decision.kind == "load_skill":
            try:
                catalog.load(decision.skill_id or "")
            except Exception:
                return False, f"unknown_skill:{decision.skill_id}"
            return True, None
        if decision.kind == "call":
            allowed = catalog.allowed_capabilities(loaded_skills)
            if decision.capability_id not in allowed:
                return False, f"capability_not_loaded:{decision.capability_id}"
            return True, None
        if decision.kind == "ready":
            return True, None
        return False, f"unknown_decision_kind:{decision.kind}"

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
            LLMMessage(role="system", content=self.SYSTEM + self.DSL_SYSTEM_ADDENDUM),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]
        failures: list[str] = []
        for attempt in range(4):
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
            raw = str(response.choices[0].message.content or "")
            decision = self._decode_any(raw)
            if decision is not None:
                allowed, reason = self._decision_allowed(
                    decision,
                    catalog=catalog,
                    loaded_skills=loaded_skills,
                )
                if allowed:
                    return decision
                failures.append(reason or "decision_not_allowed")
            else:
                failures.append("invalid_json_and_dsl_decision")
            messages.extend(
                [
                    LLMMessage(role="assistant", content=raw or "{}"),
                    LLMMessage(role="user", content=self.DSL_REPAIR),
                ]
            )
        raise V4ContractError(f"planner failed robust bounded repair: {failures}")


class RobustReliableAgentCoreV4Runtime(ReliableAgentCoreV4Runtime):
    """Reliable V4 runtime using the provider-robust decision transport."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        inherited_system = self.planner.SYSTEM
        max_steps = self.planner.max_steps
        self.planner = RobustSkillNativePlannerV4(
            self.llm,
            model=self.model,
            max_steps=max_steps,
        )
        # Preserve generalized reliability guidance already added by the reliable
        # runtime (context-scoped identity, canonical lookup binding, etc.).
        self.planner.SYSTEM = inherited_system
