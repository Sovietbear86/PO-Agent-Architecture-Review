"""Harness runtime variant that exposes source failures as typed responses."""
from __future__ import annotations

import time
import uuid

from po_agent.adapters.task_api import AS21CapabilityUnavailable, AS21SourceError, AS21SourceUnavailable

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .runtime import HarnessRuntime


class SourceAwareHarnessRuntime(HarnessRuntime):
    """Production runtime: source outage must never look like an empty portfolio."""

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        started = time.perf_counter()
        trace = str(uuid.uuid4())
        session = request.session_id or str(uuid.uuid4())
        query = request.query.strip()
        if not query:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace,
                session_id=session,
                answer="Пустой запрос.",
                warnings=["query_empty"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        try:
            intent, arguments = self.router.route(query)
            skill = self.skills.resolve(intent)
            result = await self.capabilities.execute(skill.capability_id, arguments)
            return HarnessResponse(
                status=ResponseStatus.COMPLETED,
                trace_id=trace,
                session_id=session,
                answer=result.answer,
                intent=intent,
                skill_id=skill.id,
                skill_version=skill.version,
                data=result.data,
                evidence=result.evidence,
                warnings=result.warnings,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except AS21CapabilityUnavailable:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace,
                session_id=session,
                answer="Источник AS21 не предоставляет данные, необходимые для этого запроса.",
                warnings=["source_capability_unavailable"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except AS21SourceUnavailable:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace,
                session_id=session,
                answer="Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат.",
                warnings=["source_unavailable"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except AS21SourceError:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace,
                session_id=session,
                answer="Источник AS21 вернул некорректные данные.",
                warnings=["source_protocol_error"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace,
                session_id=session,
                answer="Не удалось выполнить запрос.",
                warnings=["runtime_failure"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
