# Legacy Regression Debt

This file documents failures intentionally separated from the blocking Harness Recovery CI gates. The purpose is visibility, not suppression.

## Blocking gates

The following jobs must stay green:

- `backend-recovery` — current Harness vertical slices and AI-PDLC acceptance tests.
- `backend-hermetic-regression` — deterministic tests that do not require real external services or retired runtime contracts.
- `frontend` — recovery UI TypeScript/Vite build.

## Controlled retirement completed: POOrchestratorV1 tests

The following retired test modules were removed during controlled legacy cleanup:

- `tests/test_agent_full_integration.py`
- `tests/test_orchestrator_skill_integration.py`

They asserted behavior and private APIs of the retired `POOrchestratorV1` runtime. Their valuable user-facing behavioral contracts now have traceable Harness replacement coverage through:

- `tests/test_harness_legacy_behavioral_contracts.py` (Level A deterministic contracts);
- `tests/corpus/harness_acceptance_corpus.yaml` (Level B natural-language acceptance corpus);
- current Harness API / Dialogue Runtime / Team Matching tests.

The old full-integration module also contained legacy evolution/clarification smoke checks. Current equivalents are covered by dedicated Harness-era suites such as candidate lifecycle, clarification engine/loop, offline evaluation, promotion/rollback and related regression tests. Real SWTR/LLM validation remains in explicit real-service integration modules.

Retirement rule satisfied: the old orchestrator is no longer the production runtime and the relevant behaviors have replacement coverage. The files were deleted rather than skipped/xfail'ed so obsolete contracts cannot silently become part of the canonical baseline again.

## Remaining diagnostic categories

### Real-service tests

Files:

- `tests/test_integration_real_services.py`
- `tests/test_llm_real_integration.py`

Reason: these require real credentials and/or external SWTR/Qwen service availability. They are integration tests, not hermetic regression tests. They must run only in an explicitly configured environment with secrets and service availability checks.

### Legacy frontend structure

File:

- `tests/test_frontend_config.py`

Reason: historical assertions target the old `frontend/src/components/Layout.tsx`. The recovery UI uses a new workspace shell. Useful navigation/structure assertions must be migrated to the current workspace rather than recreating obsolete files solely to satisfy tests.

### Remaining hermetic incompatibilities

Any deterministic failure in the current Harness path is blocking and must be fixed or migrated; it must not be hidden in the diagnostic lane. Known historical candidates have included fixture assumptions, old ContextResolver expectations, and legacy EvalRunner entity extraction behavior.

## Retirement rule

A legacy test may be removed only when one of the following is true:

1. its behavior is covered by a current Harness acceptance/eval case;
2. it tests a retired component that is no longer reachable from the product;
3. it has been converted to an explicit real-service integration test.

No failure is considered resolved merely because it was moved to the diagnostic job.
