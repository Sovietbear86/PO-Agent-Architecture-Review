"""Hermes-inspired capability registry for Agent Core v3.

The registry is deliberately small and deterministic: capabilities register their
contracts and compact discovery metadata once, while execution and source access
remain in their dedicated executors/adapters.  H1A removes the pilot-local hard
coded capability table and creates the catalog H1B/H1C can use for agent-loop
selection and progressive loading.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .agent_core_v3 import (
    AgentCoreV3ContractError,
    AgentCoreV3FailureCode,
    CapabilityContractV3,
    SOURCE_AUTHORITY_REAL_AS21,
)


@dataclass(frozen=True)
class CapabilityRegistrationV3:
    """Registered capability plus compact discovery metadata.

    `intents` are semantic routing names, not entity facts. `family` and
    `summary` are intentionally compact so a later progressive-loader can expose
    the catalog without injecting every full skill contract into the LLM prompt.
    """

    contract: CapabilityContractV3
    family: str
    intents: frozenset[str]
    summary: str

    def catalog_item(self) -> dict[str, object]:
        return {
            "id": self.contract.id,
            "version": self.contract.version,
            "family": self.family,
            "intents": sorted(self.intents),
            "summary": self.summary,
            "supported_constraints": sorted(self.contract.supported_constraints),
            "source_authority": self.contract.source_authority,
        }


class CapabilityRegistryV3:
    """Self-registering deterministic catalog for Agent Core v3 capabilities."""

    def __init__(self, registrations: Iterable[CapabilityRegistrationV3] = ()) -> None:
        self._by_id: dict[str, CapabilityRegistrationV3] = {}
        self._by_intent: dict[str, str] = {}
        for registration in registrations:
            self.register(registration)

    def register(self, registration: CapabilityRegistrationV3) -> CapabilityRegistrationV3:
        capability_id = registration.contract.id.strip()
        if not capability_id:
            raise ValueError("Capability id must not be empty")
        if capability_id in self._by_id:
            raise ValueError(f"Capability already registered: {capability_id}")
        if not registration.intents:
            raise ValueError(f"Capability {capability_id} must declare at least one intent")
        for intent in registration.intents:
            normalized = str(intent).strip()
            if not normalized:
                raise ValueError(f"Capability {capability_id} contains an empty intent")
            owner = self._by_intent.get(normalized)
            if owner is not None:
                raise ValueError(f"Intent {normalized} already owned by capability {owner}")
        self._by_id[capability_id] = registration
        for intent in registration.intents:
            self._by_intent[str(intent).strip()] = capability_id
        return registration

    def get(self, capability_id: str) -> CapabilityRegistrationV3:
        try:
            return self._by_id[capability_id]
        except KeyError as exc:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                f"Unknown Agent Core v3 capability {capability_id}",
                details={"capability_id": capability_id},
            ) from exc

    def resolve_intent(self, intent: str) -> CapabilityRegistrationV3:
        normalized = str(intent or "").strip()
        capability_id = self._by_intent.get(normalized)
        if capability_id is None:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                f"No Agent Core v3 capability registered for intent {normalized or '<empty>'}",
                details={"intent": normalized},
            )
        return self._by_id[capability_id]

    def compact_catalog(self, *, family: str | None = None) -> tuple[dict[str, object], ...]:
        items = self._by_id.values()
        if family is not None:
            items = [item for item in items if item.family == family]
        return tuple(item.catalog_item() for item in sorted(items, key=lambda item: item.contract.id))

    def __len__(self) -> int:
        return len(self._by_id)



def build_h1_task_registry() -> CapabilityRegistryV3:
    """Certified H1 task-family registry used by the current v3 pilot.

    No people, spaces, task IDs or counts are registered here.  The registry
    contains only reusable capability contracts; business entities stay source
    grounded from REAL AS21 at execution time.
    """

    source = SOURCE_AUTHORITY_REAL_AS21
    return CapabilityRegistryV3(
        (
            CapabilityRegistrationV3(
                contract=CapabilityContractV3(
                    id="task-lookup-v3",
                    version="3.1.0-h1a",
                    supported_constraints=frozenset({"task_key"}),
                    source_authority=source,
                    executor_id="task_lookup_executor_v3",
                    oracle_id="direct_mcp_read_unit",
                ),
                family="tasks",
                intents=frozenset({"task_lookup"}),
                summary="Read one task by canonical task key from authoritative AS21.",
            ),
            CapabilityRegistrationV3(
                contract=CapabilityContractV3(
                    id="task-search-v3",
                    version="3.1.0-h1a",
                    supported_constraints=frozenset({"assignee", "space", "status"}),
                    source_authority=source,
                    executor_id="task_search_executor_v3",
                    oracle_id="direct_mcp_task_search",
                ),
                family="tasks",
                intents=frozenset({"task_search"}),
                summary="Search authoritative AS21 tasks by grounded assignee, space and status constraints.",
            ),
        )
    )
