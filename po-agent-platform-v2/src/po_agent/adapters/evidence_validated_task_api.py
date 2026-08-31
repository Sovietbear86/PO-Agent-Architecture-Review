"""Final real-data source validation layer for PO Harness.

A successful SWTR HTTP response is not evidence that a sprint exists: the
current facade echoes an arbitrary requested sprint_id. Existence is therefore
proven by source-backed sprint membership rows, not by echo text.
"""
from __future__ import annotations

from .hardened_production_task_api import HardenedProductionTaskApiAS21Adapter


class EvidenceValidatedProductionTaskApiAS21Adapter(HardenedProductionTaskApiAS21Adapter):
    # Production runtime uses this concrete adapter. REAL AS21 QA proved the
    # task-history read path, so history must be advertised here even though the
    # hardened parent currently overrides its own fact set.
    source_facts = frozenset(set(HardenedProductionTaskApiAS21Adapter.source_facts) | {"history"})

    async def sprint_exists(self, sprint_id: str) -> bool:
        normalized = (sprint_id or "").strip()
        if not normalized:
            return False
        # get_sprint_tasks uses complete=true and validates canonical task codes.
        # An empty corpus is UNKNOWN/non-proven, not proof of existence. This is
        # intentionally fail-closed until SWTR exposes an authoritative sprint
        # directory endpoint.
        tasks = await super().get_sprint_tasks(normalized)
        return bool(tasks)