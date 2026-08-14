# Legacy / Reference Boundary

The repository intentionally retains selected S21 and pre-Harness implementation code because it contains useful domain examples, historical SWTR integration knowledge and natural-language phrases used to build the new acceptance corpus.

It is **not** the production orchestration contract for PO Agent Platform v2.

## Reference-only components

The old `po_agent.orchestration` implementation, including `POOrchestratorV1`, its keyword/regex routing and associated legacy integration tests, is superseded by the Harness runtime.

Old S21 agent sources are retained only to:

- recover useful user-language examples;
- compare business behavior during migration;
- understand existing SWTR/task-api integration conventions;
- preserve historical evidence until the real-data pilot is complete.

Do not fix Harness language failures by adding surname declension tables or one-off regex rules to the old orchestrator. Natural-language interpretation belongs to the semantic LLM layer; source identifiers and business facts belong to deterministic grounding.

## Canonical runtime

The accepted path is built through `po_agent.harness.runtime_factory` and exposed by the v2 API. The required architecture is documented in `docs/architecture/HARNESS_DIALOGUE_LEARNING_CONTRACT.md`.

## Test policy

Legacy/environment-dependent tests are manual diagnostics. The blocking contract is the Harness recovery suite, hermetic regression and frontend build in `.github/workflows/harness-recovery-ci.yml`.

A future cleanup may remove additional legacy implementation after real SWTR/Qwen acceptance proves that no migration dependency remains.
