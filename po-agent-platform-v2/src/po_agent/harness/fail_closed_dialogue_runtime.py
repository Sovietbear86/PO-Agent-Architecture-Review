"""Fail-closed production dialogue boundary for verified negative lookups."""
from __future__ import annotations

import re

from .contracts import ResponseStatus
from .dialogue_runtime import SemanticFrame
from .semantic_authorization import IntentPreservingDialogueHarnessRuntime


class FailClosedIntentPreservingDialogueHarnessRuntime(IntentPreservingDialogueHarnessRuntime):
    """Turn source-backed negative entity results into FAILED, never COMPLETED.

    Capabilities may intentionally return structured negative evidence (for
    example {found: false}) instead of raising. The user-facing Harness must not
    label such a result as successful execution.
    """

    _EXPLICIT_SPRINT_ID_RE = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-SPRNT-\d+\b", re.I)

    @staticmethod
    def _enrich_explicit_task_key(frame: SemanticFrame, original_query: str) -> SemanticFrame:
        """Never reinterpret the suffix of an explicit sprint id as a task key.

        The base dialogue runtime deliberately enriches explicit task keys from
        raw user text. A token such as ``DMS-SPRNT-1`` previously also matched
        the generic task-key regex as ``SPRNT-1``. That corrupted a valid sprint
        query into a task lookup. Explicit sprint identifiers are source IDs of
        a different entity type and therefore take precedence.
        """
        if FailClosedIntentPreservingDialogueHarnessRuntime._EXPLICIT_SPRINT_ID_RE.search(original_query):
            return frame
        return IntentPreservingDialogueHarnessRuntime._enrich_explicit_task_key(frame, original_query)

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
