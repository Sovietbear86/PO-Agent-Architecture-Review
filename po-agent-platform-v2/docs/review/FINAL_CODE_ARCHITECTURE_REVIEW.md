# Final Code & Architecture Review — PO Agent Platform v2

Status: **READY FOR REAL-DATA PILOT, NOT YET PRODUCTION-ACCEPTED**

## Review scope

This review covers the `chatgpt-harness-recovery` implementation intended to replace the legacy PO/S21 orchestration path. The review explicitly separates the new Harness runtime from reference/legacy code and from environment-dependent integrations that cannot be validated in GitHub Actions.

## Target architecture

The accepted production direction is:

`User -> Dialogue Harness -> LLM Semantic Interpreter -> Grounded Entity/Policy Resolver -> Clarification Gate -> Versioned Skill -> deterministic Capability/Metrics Engine -> Evidence -> Response -> Feedback -> governed AI-PDLC loop`

The LLM is an interpretation layer, not a source of truth. It may normalize language, grammatical forms, shorthand and intent, but it must not invent AS21 identifiers, team logins, statuses, sprint/release IDs, source facts or numeric metrics.

## Findings

### P0 — blocking/security

No known P0 remains in the new Harness runtime after cleanup. Local auth/session configuration, tracked virtual environment/IDE state and the broken `mcp-swtr` gitlink have been removed from the recovery branch. TLS verification is enabled by default in the real LLM path and API keys are environment-supplied.

### P1 — must be proven in the real-data pilot

1. **Real SWTR/AS21 connectivity is not accepted yet.** CI validates the Task API adapter contract with hermetic/mocked sources, not the corporate network and authentication path.
2. **Real Qwen semantic quality is not accepted yet.** The JSON contract, confidence gate, grounding and clarification behavior are covered hermetically, but the enterprise Qwen endpoint/model must pass the natural-language corpus on the deployment workstation.
3. **Source capability completeness is environment-dependent.** History, attachments, sprint snapshots, competency profiles and release timelines must be advertised only when their source is genuinely available.
4. **Persistence/retention policy must be checked in the deployment environment.** Learned semantics, operational history, feedback and eval stores must use approved locations and retention settings.

These are pilot gates, not reasons to reintroduce regex routing or fake source data.

### P2 — non-blocking debt

- Legacy `POOrchestratorV1` and old S21 tests remain useful as reference/test-language material but are not the production runtime contract.
- Legacy environment-dependent tests should be retained only in a clearly diagnostic/manual suite; they must not define correctness of the new Harness.
- Performance/load targets should be baselined against the real Qwen and SWTR latency profile.
- UI end-to-end browser automation can be expanded after real-data wiring is stable.

## Architecture verdict

### Harness properties confirmed by hermetic tests

- 54 canonical Skills are versioned and covered by the acceptance corpus.
- deterministic calculations live outside the LLM.
- source failures fail closed instead of becoming empty datasets.
- source readiness distinguishes implemented Skills from currently available Skills.
- ambiguous/low-confidence natural-language interpretation can return `NEEDS_CLARIFICATION`.
- clarification is multi-turn and isolated by session.
- entity candidates are checked against source-backed team/sprint/release/status facts.
- composite task filters are executed together deterministically.
- responses carry trace/evidence and record whether the LLM was used.
- corrective feedback can create eval candidates without silently rewriting production behavior.
- learned business semantics are versioned; conflicting definitions require governance rather than silent overwrite.

## CI evidence at pre-cleanup checkpoint

Recovery CI run #259 completed successfully for all blocking gates:

- `backend-recovery`: PASS
- `backend-hermetic-regression`: PASS
- `frontend`: PASS
- `backend-legacy-diagnostic`: non-blocking failure caused by legacy/env-dependent tests (missing real LLM credentials, unavailable SWTR, obsolete legacy orchestrator/frontend expectations)

A fresh run is required after repository cleanup. It must reproduce all three blocking PASS results before pilot handoff.

## Merge decision

**Do not merge yet.** First complete the real-data pilot with Qwen + SWTR using the dedicated acceptance checklist. A failed environment/auth/source test must be classified as such; it must not be “fixed” by weakening tests, inventing source data, disabling TLS or broad-refactoring the Harness.

If the real-data pilot passes the mandatory gates, this review can be promoted from `READY FOR REAL-DATA PILOT` to `READY FOR MERGE`.
