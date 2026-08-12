"""Executable harness core for PO Agent Platform.

This package is the recovery runtime. Business capabilities are executed through
registered, allow-listed skills instead of intent-specific branches in the
orchestrator.
"""

from .contracts import (
    CapabilityResult,
    Evidence,
    HarnessRequest,
    HarnessResponse,
    ResponseStatus,
)
from .runtime import HarnessRuntime, build_fake_runtime

__all__ = [
    "CapabilityResult",
    "Evidence",
    "HarnessRequest",
    "HarnessResponse",
    "ResponseStatus",
    "HarnessRuntime",
    "build_fake_runtime",
]
