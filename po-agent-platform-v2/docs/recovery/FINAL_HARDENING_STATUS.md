# Final Hardening Status — PO Agent Platform v2

## Scope

This document is the release/merge-readiness checkpoint for the recovered Harness implementation on `chatgpt-harness-recovery`.

## Product gates

| Gate | Status | Notes |
|---|---|---|
| Canonical Skill catalog | PASS | 54 Skills implemented; source readiness is evaluated separately. |
| Deterministic metrics | PASS | Sprint/team/release/PO metrics are code-calculated, not LLM-calculated. |
| AS21 boundary | PASS | `TaskApiAS21Adapter` is async and fail-closed. |
| Source readiness | PASS | Missing history/attachments/snapshots/competencies/timeline are explicit. |
| Task-api E2E contract | PASS | Mocked HTTP -> adapter -> Harness -> API response acceptance coverage. |
| Failure semantics | PASS | Source outage, unsupported capability and malformed protocol are typed failures. |
| Operational history | PASS | Append-only execution trace with versions/evidence/warnings. |
| Session context | PASS | Scoped separately from operational history. |
| Feedback/eval loop | PASS | Explicit feedback can seed versioned eval cases. |
| Failure mining | PASS | Deterministic clustering of repeated eval failures. |
| Improvement candidate | PASS | Candidates are inert drafts (`apply=false`). |
| Shadow/offline evaluation | PASS | Baseline and candidate evaluated on the same corpus. |
| Regression gate | PASS | Default policy permits zero regressions and requires measurable improvement. |
| Human approval | PASS | Promotion requires explicit approval. |
| Version promotion/rollback | PASS | Auditable and reversible. |
| Recovery frontend build | PASS | TypeScript + Vite production build is a blocking CI gate. |
| Hermetic backend regression | PASS | Blocking CI gate without real external services. |
| Legacy full suite | DIAGNOSTIC | Non-blocking by design; contains real-service and retired-contract debt. |

## Runtime modes

### `fake`

Use for deterministic development, acceptance tests and UI work. It advertises tasks, sprints, releases, history and attachment fixtures.

### `task-api`

Production-facing boundary. It advertises only source facts actually proven by the current task-api contract: tasks, sprints and releases. Declared team profiles are injected from canonical `team_members.yaml` when available.

Do not treat unavailable source facts as empty data.

## Source-gated Skills

The code implementation exists for all canonical Skills, but runtime availability depends on facts:

- task history / time-in-status / cycle-time / lead-time require `history`;
- attachment search requires `attachments`;
- sprint carryover and scope change require `sprint_snapshots`;
- competency match and assignee recommendation require `team_competencies`;
- release forecast requires `release_timeline`.

This distinction is intentional: `implemented != source-ready`.

## External prerequisites before real AS21 acceptance

1. Start a task-api instance that can reach the target SWTR/AS21 environment.
2. Set `AS21_MODE=task-api` and `TASK_API_BASE_URL`.
3. Provide `TEAM_CONFIG_PATH` or place canonical `team_members.yaml` at an auto-probed location.
4. Run `GET /api/v1/health` and confirm `source_status=healthy`.
5. Execute the real-data checklist against permitted team spaces/products.
6. Do not enable history/attachment/snapshot/timeline readiness until those source contracts are backed by actual APIs or persisted facts.

## Merge caveat

The recovery branch was created through a long strangler rebuild and currently diverges from `clean-public-release`. Before final merge/PR approval, sync or explicitly review the current base delta rather than force-moving refs. The recovery implementation must not overwrite unrelated upstream changes.

## Definition of done for this recovery

The recovery itself is considered complete when:

- blocking recovery, hermetic regression and frontend CI are green on the final head;
- documentation and `.env.example` match runtime behaviour;
- branch/base delta is reviewed;
- real AS21 acceptance is executed when the external environment is available;
- no source-dependent Skill is advertised ready without its source fact.

Real AS21 credentials/connectivity are an environment prerequisite, not a reason to fake product behaviour in code.
