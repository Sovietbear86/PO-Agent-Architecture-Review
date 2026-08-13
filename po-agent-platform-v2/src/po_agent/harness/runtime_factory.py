"""Runtime construction for fake and production AS21 sources."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from po_agent.adapters import FakeAS21Adapter, TaskApiAS21Adapter
from po_agent.adapters.as21 import AS21Adapter

from .runtime import HarnessRuntime
from .source_readiness import SourceReadinessReport, build_source_readiness

RuntimeMode = Literal["fake", "task-api"]


@dataclass(frozen=True)
class RuntimeBundle:
    mode: RuntimeMode
    runtime: HarnessRuntime
    adapter: AS21Adapter
    readiness: SourceReadinessReport


def build_runtime_bundle(
    mode: str = "fake",
    *,
    task_api_base_url: str = "http://localhost:8003",
    task_api_timeout_seconds: float = 30.0,
) -> RuntimeBundle:
    normalized = mode.strip().lower()
    if normalized == "fake":
        adapter: AS21Adapter = FakeAS21Adapter()
        selected: RuntimeMode = "fake"
    elif normalized in {"task-api", "task_api", "real"}:
        adapter = TaskApiAS21Adapter(
            base_url=task_api_base_url,
            timeout_seconds=task_api_timeout_seconds,
        )
        selected = "task-api"
    else:
        raise ValueError(f"Unsupported PO_AGENT_AS21_MODE: {mode}")

    return RuntimeBundle(
        mode=selected,
        runtime=HarnessRuntime(adapter),
        adapter=adapter,
        readiness=build_source_readiness(adapter),
    )
