#!/usr/bin/env python3
"""Phase 1/4 tracer for semantic correction boundaries A-I."""

import asyncio
import sys
sys.path.insert(0, 'po-agent-platform-v2/src')

from po_agent.harness import (
    semantic_core_v2,
    semantic_slot_recovery,
    production_entity_grounding_v2,
    semantic_correction_runtime_v2,
)
from po_agent.harness.dialogue_runtime import SemanticFrame
from po_agent.llm.client import LLMMessage

# Capture boundaries
traces = []

def capture_boundary(name: str, frame: SemanticFrame, query: str = ""):
    """Capture semantic state at boundary."""
    slots = frame.slots if frame else {}
    traces.append({
        "boundary": name,
        "query": query[:80] if query else "",
        "slots": {
            "person_raw": slots.get("person_raw", "N/A"),
            "member_login": slots.get("member_login", "N/A"),
            "sprint_id": slots.get("sprint_id", "N/A"),
            "sprint_raw": slots.get("sprint_raw", "N/A"),
            "status_raw": slots.get("status_raw", "N/A"),
            "status_semantic": slots.get("status_semantic", "N/A"),
            "dialogue_act": slots.get("dialogue_act", "N/A"),
            "canonical_query": frame.canonical_query if frame else "N/A",
        }
    })

# Patch ConversationAwareSemanticInterpreter
original_interpret = semantic_core_v2.ConversationAwareSemanticInterpreter.interpret

async def traced_interpret(self, query: str, *, context=None):
    ctx = dict(context or {})
    session = str(ctx.get("session_id") or "")
    
    # Boundary B: cached previous semantic frame before correction
    prev_frame = self._last.get(session) if session else None
    
    frame = await original_interpret(self, query, context=ctx)
    
    # Capture boundary A: semantic interpretation output
    capture_boundary("A", frame, query)
    
    # Capture boundary B: previous frame
    if prev_frame:
        prev_sem = SemanticFrame(
            canonical_query=prev_frame.get("canonical_query", ""),
            intent_hint=prev_frame.get("intent_hint"),
            slots=prev_frame.get("slots", {}),
            clarifications=[],
            confidence=0.0,
            llm_used=False,
        )
        capture_boundary("B", prev_sem, query)
    
    # Boundary F: cache state after interpretation
    if session and session in self._last:
        cached = self._last[session]
        cached_frame = SemanticFrame(
            canonical_query=cached.get("canonical_query", ""),
            intent_hint=cached.get("intent_hint"),
            slots=dict(cached.get("slots", {})),
            clarifications=[],
            confidence=0.0,
            llm_used=False,
        )
        capture_boundary("F", cached_frame, query)
    
    return frame

semantic_core_v2.ConversationAwareSemanticInterpreter.interpret = traced_interpret

# Patch ProductionEntityResolverV2
original_ground = production_entity_grounding_v2.ProductionEntityResolverV2.ground

async def traced_ground(self, frame: SemanticFrame, original_query: str) -> SemanticFrame:
    capture_boundary("H", frame, original_query)
    result = await original_ground(self, frame, original_query)
    capture_boundary("I", result, original_query)
    return result

production_entity_grounding_v2.ProductionEntityResolverV2.ground = traced_ground

# Patch SemanticCorrectionRuntimeV2
original_process = semantic_correction_runtime_v2.SemanticCorrectionRuntimeV2.process

async def traced_process(self, request):
    session = request.session_id or ""
    current = (request.query or "").strip()
    
    # Capture before processing
    if session and session in self._last:
        prev = self._last[session]
        prev_frame = SemanticFrame(
            canonical_query=prev.query,
            intent_hint="task_search",
            slots={},
            clarifications=[],
            confidence=0.0,
            llm_used=False,
        )
        capture_boundary("C", prev_frame, current)
    
    result = await original_process(self, request)
    return result

semantic_correction_runtime_v2.SemanticCorrectionRuntimeV2.process = traced_process

# Run test
import httpx

def query(query_text, session_id="test"):
    resp = httpx.post(
        "http://127.0.0.1:8004/api/v1/query",
        json={"query": query_text, "session_id": session_id},
        timeout=30
    )
    return resp.json()

async def run_test():
    global traces
    traces = []
    
    # Session 1
    print("=== Session 1 ===")
    traces = []
    
    r1 = query("Покажи задачи Гаранина в DMS со статусом todo", "corr_072_s1")
    print(f"Turn 1: {r1.get('status')}")
    print(f"Slots: {r1.get('data', {}).get('semantic_frame', {})}")
    
    r2 = query("Покажи задачи Гаранина в DMS со статусом in progress", "corr_072_s1")
    print(f"Turn 2: {r2.get('status')}")
    print(f"Slots: {r2.get('data', {}).get('semantic_frame', {})}")
    
    print("\nTraces:")
    for t in traces:
        print(f"  {t['boundary']}: {t['slots']}")

asyncio.run(run_test())
