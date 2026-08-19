"""Fail-closed production dialogue boundary for verified negative lookups."""
from __future__ import annotations

from .contracts import ResponseStatus
from .semantic_authorization import IntentPreservingDialogueHarnessRuntime


class FailClosedIntentPreservingDialogueHarnessRuntime(IntentPreservingDialogueHarnessRuntime):
    """Turn source-backed negative entity results into FAILED, never COMPLETED.

    Capabilities may intentionally return structured negative evidence (for
    example {found: false}) instead of raising. The user-facing Harness must not
    label such a result as successful execution.
    """

    async def _execute_frame(self, frame, session, started):
        response = await super()._execute_frame(frame, session, started)
        if response.status != ResponseStatus.COMPLETED or not isinstance(response.data, dict):
            return response

        if response.data.get("found") is False:
            response.status = ResponseStatus.FAILED
            if "entity_not_found" not in response.warnings:
                response.warnings.append("entity_not_found")
            meta = response.data.setdefault("_harness", {})
            if isinstance(meta, dict):
                meta["execution_ready"] = False
                meta["negative_source_result"] = True
        return response
