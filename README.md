# PO Agent Platform v2 — Harness Architecture

This branch contains the recovery/rebuild of the PO Agent as a dialogue-first Harness agent.

## Canonical implementation

The application being accepted is in [`po-agent-platform-v2/`](po-agent-platform-v2/).

Production direction:

`User -> Dialogue Harness -> LLM Semantic Interpreter -> source-backed Grounding -> Clarification Gate -> versioned Skill -> deterministic Capability/Metrics -> Evidence -> Feedback -> governed AI-PDLC`

The LLM interprets natural language. It is **not** a source of AS21/SWTR facts and must not invent identifiers, statuses, team members or numeric metrics. Uncertainty is resolved through a user clarification turn.

## Start here

- [`PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md`](PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md) — original product/master specification retained as design input.
- [`po-agent-platform-v2/README.md`](po-agent-platform-v2/README.md) — current application/runtime documentation.
- [`po-agent-platform-v2/docs/architecture/HARNESS_DIALOGUE_LEARNING_CONTRACT.md`](po-agent-platform-v2/docs/architecture/HARNESS_DIALOGUE_LEARNING_CONTRACT.md) — mandatory dialogue/learning contract.
- [`po-agent-platform-v2/docs/review/FINAL_CODE_ARCHITECTURE_REVIEW.md`](po-agent-platform-v2/docs/review/FINAL_CODE_ARCHITECTURE_REVIEW.md) — current review verdict and open real-data gates.
- [`po-agent-platform-v2/docs/testing/COMPREHENSIVE_AGENT_TEST_PLAN.md`](po-agent-platform-v2/docs/testing/COMPREHENSIVE_AGENT_TEST_PLAN.md) — complete test strategy.
- [`po-agent-platform-v2/docs/operations/REAL_DATA_PILOT_ACCEPTANCE_CHECKLIST.md`](po-agent-platform-v2/docs/operations/REAL_DATA_PILOT_ACCEPTANCE_CHECKLIST.md) — controlled Qwen + SWTR pilot checklist.
- [`po-agent-platform-v2/docs/testing/GIGACODE_QWENCODER_REAL_DATA_RUNBOOK.md`](po-agent-platform-v2/docs/testing/GIGACODE_QWENCODER_REAL_DATA_RUNBOOK.md) — required GigaCode CLI/QwenCoder deployment, testing, failure triage and ChatGPT handoff procedure.

## Test contract

The blocking GitHub workflow is `.github/workflows/harness-recovery-ci.yml` and contains only:

1. Harness recovery/acceptance tests;
2. hermetic backend regression;
3. frontend typecheck/build.

Legacy and environment-dependent tests are intentionally isolated in `.github/workflows/legacy-diagnostic.yml` and run manually. They are reference debt, not the correctness contract for the new Harness.

The natural-language acceptance corpus is `po-agent-platform-v2/tests/corpus/harness_acceptance_corpus.yaml` and covers all 54 canonical Skills.

All local real-data/QwenCoder validation must be launched through `po-agent-platform-v2/tools/diagnostic_runner.py`. It stores a local raw log plus a redacted `sanitized.log` and machine-readable `summary.json` under `.artifacts/diagnostics/<run_id>/`. `.artifacts/` is gitignored. Only sanitized diagnostics are intended for external review or upload to ChatGPT.

## Repository hygiene

Do not commit virtual environments, IDE state, local GigaCode settings, `.env`, MCP configs containing credentials, tokens, certificates, logs, archives, real SWTR data snapshots or generated reports. `.gigacode/agents` and `.gigacode/skills` are intentional project assets; local `.gigacode/settings.json` is not.

## Current release state

The code is **ready for a controlled real-data pilot**, not yet production-accepted. Real enterprise Qwen and SWTR/AS21 connectivity/capability tests must pass before merge/release approval. A failure caused by environment, authentication, network, source availability or source data must not be hidden by changing Harness business logic.
