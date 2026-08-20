from __future__ import annotations

import pytest

from po_agent.harness.core8_semantic_precision import Core8SemanticPrecisionInterpreter
from po_agent.harness.dialogue_runtime import SemanticFrame
from po_agent.harness.fail_closed_dialogue_runtime import FailClosedIntentPreservingDialogueHarnessRuntime


class BadSprintDelegate:
    """Model the exact provider degradation observed in QA 019 rerun."""

    async def interpret(self, query: str, *, context=None) -> SemanticFrame:
        return SemanticFrame(
            canonical_query="покажи задачу {task_key}",
            intent_hint="task_lookup",
            slots={"task_key": "SPRNT-1", "person_raw": "Гаранина"},
            confidence=0.9,
            llm_used=True,
        )


@pytest.mark.asyncio
async def test_full_dms_sprint_id_is_preserved_and_task_lookup_repaired():
    interpreter = Core8SemanticPrecisionInterpreter(BadSprintDelegate())
    frame = await interpreter.interpret("Покажи задачи Гаранина в DMS-SPRNT-1")

    assert frame.intent_hint == "task_search"
    assert frame.slots["sprint_id"] == "DMS-SPRNT-1"
    assert "task_key" not in frame.slots


@pytest.mark.asyncio
async def test_full_olp_sprint_id_is_generic_not_dms_hardcoded():
    interpreter = Core8SemanticPrecisionInterpreter(BadSprintDelegate())
    frame = await interpreter.interpret("Покажи задачи Гаранина в OLP-SPRNT-17")

    assert frame.intent_hint == "task_search"
    assert frame.slots["sprint_id"] == "OLP-SPRNT-17"
    assert "task_key" not in frame.slots


def test_dialogue_enrichment_does_not_extract_sprint_suffix_as_task_key():
    frame = SemanticFrame(
        canonical_query="покажи задачи",
        intent_hint="task_search",
        slots={"sprint_id": "DMS-SPRNT-1"},
    )
    enriched = FailClosedIntentPreservingDialogueHarnessRuntime._enrich_explicit_task_key(
        frame,
        "Покажи задачи Гаранина в DMS-SPRNT-1",
    )

    assert enriched.slots == {"sprint_id": "DMS-SPRNT-1"}


def test_real_task_key_still_enriches_normally():
    frame = SemanticFrame(canonical_query="покажи задачу", intent_hint="task_lookup")
    enriched = FailClosedIntentPreservingDialogueHarnessRuntime._enrich_explicit_task_key(
        frame,
        "Покажи задачу DMS-348",
    )

    assert enriched.slots["task_key"] == "DMS-348"
