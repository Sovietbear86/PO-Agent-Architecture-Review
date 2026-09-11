"""Reliability overlay for the Agent Core v4 skill-native POC.

This module fixes generalized runtime seams found by Assignment 176 without
re-introducing semantic-prepass, surname rules, phrase routers or entity facts.

Rules:
- team roster is an authorization/scope hint, REAL AS21 remains identity truth;
- a person may also be resolved inside an authoritative task context (for example
  a sprint) when a global source search is ambiguous;
- canonical values already returned by trusted observations may be re-used even
  when the planner emits the literal value instead of `$obs.N.field` syntax;
- current sprint uses the certified task source with a quoted product filter and
  full collection semantics instead of the legacy small/default scan.
"""
from __future__ import annotations

import os
import re
from typing import Any, Mapping

from po_agent.adapters.task_api import AS21SourceError, AS21SourceUnavailable

from .agent_core_v4 import (
    AgentCoreV4Runtime,
    CapabilitySpecV4,
    SkillNativePlannerV4,
    V4ContractError,
    V4NeedsClarification,
    V4Observation,
    _literal_is_query_derived,
)
from .contracts import CapabilityResult, Evidence
from .production_entity_grounding_v2 import APPROVED_PRODUCT_SPACES


class ReliableAgentCoreV4Runtime(AgentCoreV4Runtime):
    """Generalized reliability fixes for source-backed skill-native execution."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._handlers["sprint.current"] = self._sprint_current_source_backed
        self._capability_specs["member.resolve"] = CapabilitySpecV4(
            "member.resolve",
            "Resolve a human reference against REAL AS21, optionally inside a source-backed sprint/space context when global identity search is ambiguous.",
            {
                "reference": "required raw human reference",
                "sprint_id": "optional sprint id or prior sprint.resolve observation",
                "space": "optional approved product space",
            },
        )
        # Rebuild detail catalog so progressive disclosure exposes the generalized
        # contextual resolver contract without loading entity facts into prompts.
        self.catalog = self._build_skill_catalog()
        self.planner.SYSTEM = SkillNativePlannerV4.SYSTEM + """
Additional reliability rule:
- When a person reference may be globally ambiguous and the user also supplied a sprint or space, first validate the context and then pass sprint_id/space to member.resolve. Prefer authoritative context-scoped identity resolution over guessing a global identity.
"""

    @staticmethod
    def _name_tokens(value: str) -> tuple[str, ...]:
        return tuple(
            token.casefold()
            for token in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", str(value or ""))
            if len(token) >= 2
        )

    @classmethod
    def _token_equivalent(cls, left: str, right: str) -> bool:
        if left == right or left.startswith(right) or right.startswith(left):
            return True
        common = os.path.commonprefix((left, right))
        return len(common) >= min(5, len(left), len(right))

    @classmethod
    def _reference_matches_identity(cls, reference: str, *identity_values: str) -> bool:
        wanted = cls._name_tokens(reference)
        hay = cls._name_tokens(" ".join(value for value in identity_values if value))
        return bool(wanted) and all(any(cls._token_equivalent(w, h) for h in hay) for w in wanted)

    def _team_candidates(self, reference: str):
        """Resolve a natural reference against the configured authorized roster.

        This is not the source of truth for identity existence. It only narrows an
        AS21-wide search to the PO Agent team. The selected login is subsequently
        re-validated against REAL AS21 before it can be used.
        """
        direct = self.team.resolve_person(reference)
        if direct:
            return direct
        wanted = self._name_tokens(reference)
        if not wanted:
            return ()
        matches = []
        for entry in self.team.entries:
            hay = self._name_tokens(f"{entry.full_name} {entry.login}")
            if all(any(self._token_equivalent(w, h) for h in hay) for w in wanted):
                matches.append(entry)
        return tuple(matches)

    async def _resolve_source_login(self, reference: str) -> str:
        client = getattr(self.adapter, "_client", None)
        if client is None:
            matches = self._team_candidates(reference)
            if len(matches) != 1:
                raise V4NeedsClarification(
                    f"Не удалось однозначно определить пользователя «{reference}».",
                    options=tuple(item.login for item in matches),
                )
            return matches[0].login

        try:
            response = await client.get(
                "/api/v1/swtr-read/assignees/resolve",
                params={"reference": reference},
            )
            if response.status_code == 409:
                payload = response.json() if response.content else {}
                detail = payload.get("detail") if isinstance(payload, dict) else None
                matches = detail.get("matches") if isinstance(detail, dict) else []
                raise V4NeedsClarification(
                    f"Не удалось однозначно определить пользователя «{reference}».",
                    options=tuple(str(item) for item in matches if item),
                )
            response.raise_for_status()
            payload = response.json()
        except V4NeedsClarification:
            raise
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in {502, 503}:
                raise AS21SourceUnavailable("REAL AS21 identity resolver unavailable") from exc
            raise AS21SourceError("REAL AS21 identity resolver failed") from exc
        external_id = str(payload.get("external_id") or "").strip() if isinstance(payload, dict) else ""
        if not external_id:
            raise V4NeedsClarification(f"Не удалось подтвердить пользователя «{reference}» в AS21.")
        return external_id

    async def _resolve_identity_in_task_context(
        self,
        reference: str,
        *,
        sprint_id: str = "",
        space: str = "",
    ) -> str | None:
        """Resolve a person from source rows already bounded by user context.

        This is the generalized PVM-Guru-style behavior: when global user search is
        ambiguous but the question contains a sprint/space, inspect the authoritative
        task context and accept the identity only when exactly one canonical assignee
        in that context matches the natural reference. No names or ids are hardcoded.
        """
        sprint = str(sprint_id or "").strip().upper()
        product = str(space or "").strip().upper()
        if product and product not in APPROVED_PRODUCT_SPACES:
            raise V4NeedsClarification(f"Пространство «{product}» не подтверждено.")
        if not sprint:
            return None

        tasks = list(await self.adapter.get_sprint_tasks(sprint, product or None))
        matches: set[str] = set()
        for task in tasks:
            display = str(getattr(task, "assignee", None) or "").strip()
            login = str(getattr(task, "assignee_login", None) or "").strip()
            external_id = str(getattr(task, "assignee_id", None) or "").strip()
            if self._reference_matches_identity(reference, display, login, external_id):
                canonical = login or external_id
                if canonical:
                    matches.add(canonical)
        if len(matches) == 1:
            return next(iter(matches))
        if len(matches) > 1:
            raise V4NeedsClarification(
                f"В контексте {sprint} найдено несколько исполнителей для «{reference}». Кого выбрать?",
                options=tuple(sorted(matches)),
            )
        return None

    @staticmethod
    def _member_result(reference: str, external_id: str, resolution_scope: str) -> CapabilityResult:
        return CapabilityResult(
            answer=f"Пользователь подтверждён: {external_id}.",
            data={
                "reference": reference,
                "member_login": external_id,
                "external_id": external_id,
                "source": "REAL_AS21",
                "resolution_scope": resolution_scope,
            },
            evidence=[
                Evidence(
                    type="member_identity",
                    source="as21",
                    entity_id=external_id,
                    label=reference,
                    value=external_id,
                )
            ],
        )

    async def _member_resolve(self, args: dict[str, str]) -> CapabilityResult:
        reference = str(args.get("reference") or "").strip()
        sprint_id = str(args.get("sprint_id") or "").strip()
        space = str(args.get("space") or "").strip()
        if not reference:
            raise V4NeedsClarification("Кого именно нужно найти?")

        # 1) Authorized team scope is a fast disambiguation hint, not source truth.
        team_matches = self._team_candidates(reference)
        if len(team_matches) == 1:
            expected_login = team_matches[0].login
            external_id = await self._resolve_source_login(expected_login)
            if external_id.casefold() != expected_login.casefold():
                raise V4NeedsClarification(
                    f"Источник AS21 не подтвердил ожидаемый login для «{reference}».",
                    options=(external_id,),
                )
            return self._member_result(reference, external_id, "AUTHORIZED_TEAM_ROSTER")
        if len(team_matches) > 1:
            raise V4NeedsClarification(
                f"Нашёл несколько участников команды для «{reference}». Кого выбрать?",
                options=tuple(item.login for item in team_matches),
            )

        # 2) Context-scoped source resolution before global source search. This is
        # critical for names that are globally ambiguous but unique in a sprint.
        contextual = await self._resolve_identity_in_task_context(
            reference,
            sprint_id=sprint_id,
            space=space,
        )
        if contextual:
            return self._member_result(reference, contextual, "REAL_AS21_TASK_CONTEXT")

        # 3) Fall back to global REAL AS21 identity resolution.
        external_id = await self._resolve_source_login(reference)
        return self._member_result(reference, external_id, "AS21_GLOBAL")

    @staticmethod
    def _trusted_identity_values(observations: list[V4Observation]) -> set[str]:
        trusted_keys = {"member_login", "external_id", "assignee_login", "assignee_id"}
        values: set[str] = set()

        def visit(value: Any, key: str | None = None) -> None:
            if isinstance(value, Mapping):
                for nested_key, nested_value in value.items():
                    visit(nested_value, str(nested_key))
                return
            if isinstance(value, list):
                for item in value:
                    visit(item, key)
                return
            if key in trusted_keys and isinstance(value, (str, int)) and str(value).strip():
                values.add(str(value).strip().casefold())

        for observation in observations:
            visit(observation.data)
        return values

    def _reference_is_safe_normalization(self, raw: str, query: str) -> bool:
        if _literal_is_query_derived(raw, query):
            return True
        # A morphology-normalized person reference is safe only if it resolves to
        # exactly one authorized roster entry; REAL AS21 validation still happens
        # inside member.resolve before a canonical login is emitted.
        return len(self._team_candidates(raw)) == 1

    def _validate_call_literals(
        self,
        capability_id: str,
        args: Mapping[str, str],
        query: str,
        observations: list[V4Observation],
    ) -> None:
        safe_enum_fields = {"status"}
        trusted_identities = self._trusted_identity_values(observations)

        for key, value in args.items():
            raw = str(value).strip()
            if raw.startswith("$obs."):
                continue
            if key in safe_enum_fields:
                continue
            if key == "assignee":
                # The planner may repeat the canonical identity text from a trusted
                # observation instead of reproducing the exact $obs syntax. Accept
                # only byte-equivalent source-backed values, never arbitrary text.
                if raw.casefold() in trusted_identities:
                    continue
                raise V4ContractError(
                    f"{capability_id}.{key} must equal a source-backed prior observation"
                )
            if key == "reference" and capability_id == "member.resolve":
                if self._reference_is_safe_normalization(raw, query):
                    continue
                raise V4ContractError(
                    f"planner person reference is neither query-derived nor uniquely team-scoped: {raw}"
                )
            if key in {"reference", "space", "sprint_id", "release_id", "task_key", "product"}:
                if not _literal_is_query_derived(raw, query):
                    raise V4ContractError(
                        f"planner literal is not grounded in user query: {key}={raw}"
                    )

    @staticmethod
    def _sprint_sort_key(value: str) -> tuple[int, str]:
        match = re.search(r"-SPRNT-(\d+)$", str(value or ""), flags=re.I)
        return (int(match.group(1)) if match else -1, str(value or ""))

    async def _sprint_current_source_backed(self, args: dict[str, str]) -> CapabilityResult:
        product = str(args.get("product") or args.get("space") or "").strip().upper()
        if product not in APPROVED_PRODUCT_SPACES:
            raise V4NeedsClarification(
                f"Не удалось подтвердить пространство «{product or '?'}».",
                options=tuple(sorted(APPROVED_PRODUCT_SPACES)),
            )
        # Production search routing expects quoted project literals. Ask for the
        # full collection so current-sprint resolution cannot depend on a small
        # default page.
        tasks = list(
            await self.adapter.search_tasks(
                f'project = "{product}"',
                max_results=10000,
            )
        )
        sprint_ids = sorted(
            {str(task.sprint_id).strip() for task in tasks if getattr(task, "sprint_id", None)},
            key=self._sprint_sort_key,
            reverse=True,
        )
        current = sprint_ids[0] if sprint_ids else None
        return CapabilityResult(
            answer=(
                f"Текущий доступный спринт {product}: {current}."
                if current
                else f"Для {product} не найден спринт в доступных REAL AS21 данных."
            ),
            data={
                "product": product,
                "space": product,
                "sprint_id": current,
                "candidate_sprints": sprint_ids,
                "source": "REAL_AS21",
            },
            evidence=[
                Evidence(
                    type="sprint_resolution",
                    source="as21",
                    entity_id=product,
                    label="sprint_id",
                    value=current,
                )
            ],
            warnings=[] if current else ["current_sprint_not_found"],
        )
