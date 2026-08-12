# Legacy Regression Debt

This file documents failures that are intentionally separated from the blocking
Harness Recovery CI gates. The purpose is visibility, not suppression.

## Blocking gates

The following jobs must stay green:

- `backend-recovery` — new Harness vertical slices and AI-PDLC acceptance tests.
- `backend-hermetic-regression` — deterministic tests that do not require real external services or obsolete runtime contracts.
- `frontend` — recovery UI TypeScript/Vite build.

## Diagnostic legacy gate

`backend-legacy-diagnostic` runs the complete historical test suite with
`continue-on-error: true`. Failures remain visible in Actions but do not block
recovery development while old runtime paths are being strangled.

## Current known categories

### Real-service tests

Files:

- `tests/test_integration_real_services.py`
- `tests/test_llm_real_integration.py`

Reason: these instantiate `RealLLMClient` without CI credentials and/or call a
real SWTR endpoint. They are integration tests, not hermetic regression tests.
They must later move to an explicitly configured environment with secrets and
service availability checks.

### Legacy orchestrator contracts

Files:

- `tests/test_agent_full_integration.py`
- `tests/test_orchestrator_skill_integration.py`

Reason: these assert behavior of the old `POOrchestratorV1`, including its old
intent names and private method signature. The recovery runtime is
`HarnessRuntime` and is covered by its own acceptance suite. We will migrate
valuable scenarios to Harness eval/acceptance cases before deleting the legacy
orchestrator.

### Legacy frontend structure

File:

- `tests/test_frontend_config.py`

Reason: tests require the old `frontend/src/components/Layout.tsx`. The recovery
UI uses a new shell and intentionally no longer compiles the Qwen UI surface.
The useful navigation/structure assertions must be rewritten against the new
workspace shell rather than recreating obsolete files solely to satisfy tests.

### Remaining hermetic incompatibilities

The historical full run also exposed several potentially useful incompatibilities
that are not external-service related, for example:

- attachment fixture expectations around `DMS-202`;
- old `ContextResolver` clarification expectations;
- legacy entity extraction expectation in `EvalRunner`.

These remain candidates for migration or correction. If any of them fail the
new `backend-hermetic-regression` gate they become blocking and must be fixed,
not ignored.

## Retirement rule

A legacy test may be removed only when one of the following is true:

1. its behavior is covered by a new Harness acceptance/eval case;
2. it tests a retired component that is no longer reachable from the product;
3. it is converted to an explicit real-service integration test.

No failure is considered resolved merely because it was moved to the diagnostic
job.
