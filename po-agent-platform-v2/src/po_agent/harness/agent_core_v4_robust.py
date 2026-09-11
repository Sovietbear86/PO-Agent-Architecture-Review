"""Provider-robust decision protocol for Agent Core v4.

The V4 planner remains fully agentic: the LLM chooses which skill to load and
which governed capability to call next. This module hardens only the transport
of that decision so provider-specific malformed JSON cannot kill an otherwise
valid trajectory.

Primary decisions use the normal JSON contract from SkillNativePlannerV4.
Only after an undecodable primary decision may the model use a tiny typed DSL:

    LOAD <skill_id>
    CALL <capability_id> key=value key2="multi word value"

Recovery is deliberately action-only. A repair turn may never manufacture a
terminal READY decision: if the model cannot recover a valid LOAD/CALL within
the bounded attempts, the runtime fails closed. READY remains available on the
primary decision through the normal V4 JSON contract (and is still decodable if
it is emitted as primary DSL), but never as a repair shortcut.

The DSL does not bypass capability loading, observation binding, source-backed
identity checks, argument validation or postconditions. It is trajectory-agnostic
and contains no person/space/sprint/task rules.
"""
from __future__ import annotations

import json
import re
import shlex
from typing import Any

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
    """JSON-primary planner with bounded, action-only typed recovery."""

    # Do not alter the primary decision framing. Assignment 180 proved that an
    # always-on DSL/READY addendum changes Qwen's action-selection behaviour.
    # The recovery protocol is disclosed only after a primary decode failure.
    DSL_REPAIR = """The previous planner decision could not be decoded safely.
Recover the SAME next action only. Return exactly ONE action decision.
Prefer valid JSON using exactly one non-null branch: load_skill OR call.
If JSON serialization is unreliable, return exactly one DSL line:
LOAD <skill_id>
CALL <capability_id> key=value key2="multi word value"
Do NOT return READY during recovery. Do not answer the user, add prose, markdown,
or source facts. Do not invent ids. If the trajectory is not complete, continue
with the next governed skill/capability action."""

    @staticmethod
    def _clean_text(raw: str) -> str:
        text = str(raw or "").strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.I | re.S).strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:text|json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
        return text

    @classmethod
    def _decode_dsl(cls, raw: str, *, allow_ready: bool = True) -> V4Decision | None:
        text = cls._clean_text(raw)
        if not text:
            return None
        commands = r"LOAD|CALL|READY" if allow_ready else r"LOAD|CALL"
        candidate_lines = [
            line.strip()
            for line in text.splitlines()
            if re.match(rf"^(?:{commands})\b", line.strip(), flags=re.I)
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
        if command == "READY" and allow_ready:
            answer = line[len(parts[0]):].strip()
            return V4Decision("ready", answer=answer, rationale="dsl_primary") if answer else None
        return None

    @classmethod
    def _decode_any(cls, raw: str, *, allow_ready: bool = True) -> V4Decision | None:
        obj = _extract_json_object(raw)
        decision = cls._decode(obj) if obj is not None else None
        if decision is not None:
            if decision.kind == "ready" and not allow_ready:
                return None
            return decision
        return cls._decode_dsl(raw, allow_ready=allow_ready)

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
            # Keep the primary framing byte-for-byte equivalent in spirit to the
            # proven JSON-only V4 planner. Recovery instructions are added only
            # after an actual decode/governance failure.
            LLMMessage(role="system", content=self.SYSTEM),
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
            is_primary = attempt == 0
            decision = self._decode_any(raw, allow_ready=is_primary)
            if decision is not None:
                # Defense in depth: a repair turn is exclusively for restoring an
                # action decision. A terminal answer after a malformed turn is
                # ambiguous and must fail closed rather than silently truncate the
                # trajectory.
                if not is_primary and decision.kind == "ready":
                    failures.append("recovery_ready_not_permitted")
                else:
                    allowed, reason = self._decision_allowed(
                        decision,
                        catalog=catalog,
                        loaded_skills=loaded_skills,
                    )
                    if allowed:
                        return decision
                    failures.append(reason or "decision_not_allowed")
            else:
                failures.append(
                    "invalid_primary_decision" if is_primary else "invalid_recovery_action"
                )
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
