"""Harness runtime variant that exposes source failures as typed responses."""
from __future__ import annotations

import time
import uuid

from po_agent.adapters.task_api import AS21CapabilityUnavailable, AS21SourceError, AS21SourceUnavailable, TaskApiAS21Adapter

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .runtime import HarnessRuntime


class SourceAwareHarnessRuntime(HarnessRuntime):
    """Production runtime that fails closed on unavailable source facts."""

    def __init__(self, adapter, *, source_facts=None) -> None:
        super().__init__(adapter)
        self.source_facts = frozenset(source_facts or ())

    @staticmethod
    def _required_fact(query: str) -> str | None:
        text = query.casefold()
        if any(x in text for x in ("вложен", "attachment", "excel", "xlsx", "pdf", "msg")):
            return "attachments"
        if any(x in text for x in ("истори", "lifecycle", "времени в статус", "time in status", "cycle time", "lead time")):
            return "history"
        if any(x in text for x in ("carryover", "перенос", "scope change", "изменение scope", "изменение состава", "что добавили", "что убрали")):
            return "sprint_snapshots"
        if any(x in text for x in ("кто подходит для задачи", "подбор по компетенц", "кто может взять задачу", "компетенц", "рекомендуй исполнителя")):
            return "team_competencies"
        if any(x in text for x in ("release forecast", "прогноз релиза", "прогноз по релизу", "когда будет готов релиз", "когда закончим релиз")):
            return "release_timeline"
        return None

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

        required = self._required_fact(query)
        if required and required not in self.source_facts:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace,
                session_id=session,
                answer=f"Источник AS21 не предоставляет обязательные данные для этого запроса: {required}.",
                data={"missing_source_fact": required},
                warnings=["source_capability_unavailable"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )

        try:
            intent, arguments = self.router.route(query)
            skill = self.skills.resolve(intent)
            result = await self.capabilities.execute(skill.capability_id, arguments)
            if skill.id == "portfolio-overview" and isinstance(result.data, dict):
                result.data["adapter"] = "task-api" if isinstance(self.adapter, TaskApiAS21Adapter) else "fake-as21"
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
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=trace, session_id=session, answer="Источник AS21 не предоставляет данные, необходимые для этого запроса.", warnings=["source_capability_unavailable"], latency_ms=(time.perf_counter() - started) * 1000)
        except AS21SourceUnavailable:
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=trace, session_id=session, answer="Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат.", warnings=["source_unavailable"], latency_ms=(time.perf_counter() - started) * 1000)
        except AS21SourceError:
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=trace, session_id=session, answer="Источник AS21 вернул некорректные данные.", warnings=["source_protocol_error"], latency_ms=(time.perf_counter() - started) * 1000)
        except Exception:
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=trace, session_id=session, answer="Не удалось выполнить запрос.", warnings=["runtime_failure"], latency_ms=(time.perf_counter() - started) * 1000)
