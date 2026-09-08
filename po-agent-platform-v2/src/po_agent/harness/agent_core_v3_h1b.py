"""H1B processor that makes the Hermes-style loop the primary v3 control flow.

H1A's direct single-shot executor remains implemented in the parent processor for
compatibility and focused fallback experiments, but H1B production routing must
not silently truncate compound requests before the planner sees them.
"""
from __future__ import annotations

import time
import uuid

from .agent_core_v3 import AgentCoreV3ContractError
from .agent_core_v3_pilot import AgentCoreV3PilotProcessor
from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .agent_core_v3 import SessionEnvelope


class AgentCoreV3H1BProcessor(AgentCoreV3PilotProcessor):
    """Run every certified v3 task request through the bounded planner first."""

    async def process(self, request: HarnessRequest, *, envelope: SessionEnvelope) -> HarnessResponse:
        started = time.perf_counter()
        if self.loop_planner is None:
            return await super().process(request, envelope=envelope)
        try:
            return await self._run_agent_loop(request, envelope, started)
        except AgentCoreV3ContractError as exc:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=str(uuid.uuid4()),
                session_id=envelope.runtime_session_id,
                answer="Agent Core v3 остановил выполнение: план или результат не прошёл контракт безопасности.",
                data={"_agent_core_v3": {
                    "stage": "H1B",
                    "architecture_stage": "H1B_AGENT_LOOP",
                    "conversation_id": envelope.conversation_id,
                    "runtime_session_id": envelope.runtime_session_id,
                    "turn_id": envelope.turn_id,
                    "failure_code": exc.code.value,
                    "details": exc.details,
                    "capability_catalog_size": len(self.registry),
                    "execution_ready": False,
                }},
                warnings=[exc.code.value],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
